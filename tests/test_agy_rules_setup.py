"""Antigravity reviewer allow-rules: a closed list, a stored preview, a backup and per-item rules (owner, 28/11/2026)."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

from tests.data_root_fixture import account

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/setup/scripts/agy_rules_setup.py'
spec = importlib.util.spec_from_file_location('agy_rules_setup', SCRIPT)
ars = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ars)

POSTING = 'command(python3 -I ' + str((ROOT / 'skills/review-gate/scripts/post_review.py').resolve()) + ')'
STALE = 'command(python3 -I /synthetic/old-checkout/skills/fnl-review-gate/scripts/post_review.py)'
PRIVATE = 'command(synthetic-tool --token not-a-real-value)'


class AgyRulesSetupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.home = account(self, base / 'home')
        # Only the world-writable system temporary ancestors are exempted; checks on the account stay active.
        ancestors = {p.stat().st_ino for p in base.parents if p.stat().st_mode & 0o022}
        original = os.fstat
        def fstat(fd):
            info = original(fd)
            if info.st_ino in ancestors and stat.S_ISDIR(info.st_mode):
                fields = list(info)
                fields[0] &= ~0o022
                return os.stat_result(fields)
            return info
        patch = mock.patch.object(os, 'fstat', side_effect=fstat)
        patch.start()
        self.addCleanup(patch.stop)
        (self.home / '.finolabs/vibecode').mkdir(parents=True, mode=0o700)
        self.settings = self.home / '.gemini/antigravity-cli/settings.json'
        self.settings.parent.mkdir(parents=True, mode=0o700)
        self.original = {'model': 'synthetic', 'permissions': {'allow': ['command(git status)', STALE, PRIVATE],
                                                                 'deny': ['command(rm)']}}
        self.settings.write_text(json.dumps(self.original, indent=2) + '\n')
        self.settings.chmod(0o600)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch('sys.argv', ['x', *args]):
            code = ars.main()
        return code, out.getvalue(), err.getvalue()

    def preview(self, *rules):
        code, out, err = self.run_main('preview', *[a for rule in rules for a in ('--rule', rule)])
        self.assertEqual((code, err), (0, ''))
        return out, out.rsplit('Digest: ', 1)[1].strip()

    def test_preview_shows_only_our_rules_and_counts_the_rest(self):
        out, digest = self.preview('git-show', 'git-grep', 'posting')
        self.assertIn('Add: command(git show)', out)
        self.assertIn('Add: command(git grep)', out)
        self.assertIn('Add: ' + POSTING, out)
        self.assertIn('Remove: 1 post_review.py rule that points to no script of this install', out)
        self.assertIn('Other allow-rules (unchanged): 2', out)
        for leaked in ('synthetic-tool', 'not-a-real-value', '/synthetic/old-checkout', 'command(rm)'):
            self.assertNotIn(leaked, out)
        self.assertRegex(digest, r'^[0-9a-f]{64}$')
        self.assertEqual(json.loads(self.settings.read_text()), self.original)

    def test_apply_adds_rules_keeps_others_removes_the_stale_posting_rule_and_backs_up(self):
        before = self.settings.read_bytes()
        _, digest = self.preview('git-show', 'git-diff', 'posting')
        code, out, err = self.run_main('apply', '--digest', digest, '--yes')
        self.assertEqual((code, err), (0, ''), out)
        data = json.loads(self.settings.read_text())
        self.assertEqual(data['permissions']['allow'],
                         ['command(git status)', PRIVATE, 'command(git show)', 'command(git diff)', POSTING])
        self.assertEqual((data['model'], data['permissions']['deny']), ('synthetic', ['command(rm)']))
        self.assertEqual(stat.S_IMODE(self.settings.stat().st_mode), 0o600)
        [backup] = [p for p in self.settings.parent.iterdir() if p.name.startswith('settings.json.bak-')]
        self.assertEqual(backup.read_bytes(), before)
        # A second preview of the same rules changes nothing.
        out, digest = self.preview('git-show', 'git-diff', 'posting')
        self.assertIn('No change.', out)

    def test_every_rule_is_a_read_only_git_prefix_or_this_install_posting_rule(self):
        self.assertEqual(sorted(ars.RULES), ['git-blame', 'git-diff', 'git-grep', 'git-log', 'git-ls-files',
                                             'git-merge-base', 'git-rev-parse', 'git-show', 'posting'])
        for name, rule in ars.RULES.items():
            self.assertRegex(rule, r'^command\(git [a-z-]+\)$' if name != 'posting' else r'^command\(python3 -I /')
            self.assertNotRegex(rule, r'[*?;&|$`<>]')

    def test_refusals_change_nothing(self):
        before = self.settings.read_bytes()
        code, _, err = self.run_main('preview', '--rule', 'git-push')
        self.assertEqual((code, err.startswith('Antigravity rule setup refused')), (1, True))
        _, digest = self.preview('git-log')
        for args in (('apply', '--digest', digest), ('apply', '--digest', '0' * 64, '--yes')):
            code, _, err = self.run_main(*args)
            self.assertEqual(code, 1, args)
        self.settings.write_text(self.settings.read_text().replace('synthetic', 'changed'))
        changed = self.settings.read_bytes()
        code, _, err = self.run_main('apply', '--digest', digest, '--yes')
        self.assertEqual(code, 1)
        self.assertIn('preview again', err)
        self.assertEqual(self.settings.read_bytes(), changed)
        self.assertNotEqual(changed, before)
        self.assertEqual([p for p in self.settings.parent.iterdir() if '.bak-' in p.name], [])

    def test_a_missing_settings_file_is_created_private_and_a_bad_one_refused(self):
        self.settings.unlink()
        _, digest = self.preview('git-show')
        self.assertEqual(self.run_main('apply', '--digest', digest, '--yes')[0], 0)
        self.assertEqual(json.loads(self.settings.read_text()), {'permissions': {'allow': ['command(git show)']}})
        self.assertEqual(stat.S_IMODE(self.settings.stat().st_mode), 0o600)
        self.settings.write_text('{"permissions": {"allow": "not a list"}}')
        code, _, err = self.run_main('preview', '--rule', 'git-show')
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()
