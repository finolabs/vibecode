"""Heavy-job gate and its installer (docs/specs/heavy-jobs.md part D): synthetic payloads, temporary homes only."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import stat
import sys
import tempfile
import types
import unittest
from unittest import mock

from tests.data_root_fixture import account

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = load('heavy_gate_hook', ROOT / 'scripts/heavy_gate_hook.py')
setup = load('heavy_gate_setup', ROOT / 'skills/setup/scripts/heavy_gate_setup.py')

WRAPPED = 'python3 -I /abs/skills/delegate/scripts/heavy_run.py run --label t -- docker compose up --abort-on-container-exit'
DENIED = ['docker compose up', 'docker run --rm image', 'docker build .', 'docker buildx build .', 'docker-compose up',
          'playwright test', 'npx playwright test', 'pnpm exec playwright test', 'go test ./contract/...',
          'go test -run Integration ./integration/...', 'python3 -m unittest', 'python -m unittest discover -s tests',
          'python3 -m unittest tests.a tests.b tests.c', 'cd app && docker compose up', 'FOO=1 docker compose up',
          'echo start; docker compose up', 'docker compose up 2>&1 | tee log',
          WRAPPED + ' && docker compose down']
ALLOWED = [WRAPPED,
           'python3 -I /abs/scripts/run_env.py -- ' + WRAPPED,
           'FNL_DISPATCH_ID=d1 python3 -I /abs/scripts/run_env.py -- FNL_DISPATCH_ID=d1 ' + WRAPPED,
           '/abs/skills/delegate/scripts/heavy_run.py run -- docker compose up',
           './heavy_run.py run --label t --pass-env NAME --max-minutes 30 -- docker compose up',
           'cd app && python3 -I ../heavy_run.py run -- docker build .',
           'ls -la', 'docker ps', 'go test ./...', 'python3 -m unittest tests.test_a tests.test_b',
           'npx eslint .', 'git commit -m "docker compose up"', 'echo docker compose up',
           # Not classified with certainty: allowed.
           'cat <<EOF\ndocker compose up\nEOF', 'echo $(docker compose up)', '(docker compose up)',
           'env docker compose up', 'docker compose up "unclosed']


class GateTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = account(self, Path(temp.name) / 'home')
        self.root = self.home / '.finolabs/vibecode'
        self.root.mkdir(parents=True, mode=0o700)
        env = mock.patch.dict(os.environ, {}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def host(self, text):
        (self.root / 'host.md').write_text(text)

    def run_hook(self, payload, raw=None):
        data = raw if raw is not None else json.dumps(payload).encode()
        written = []
        stdin = types.SimpleNamespace(buffer=io.BytesIO(data))
        with mock.patch.object(sys, 'stdin', stdin), \
                mock.patch.object(hook.os, 'write', side_effect=lambda fd, b: written.append((fd, b))), \
                mock.patch.object(hook.signal, 'alarm'), mock.patch.object(hook.signal, 'signal'):
            code = hook.main()
        self.assertEqual(code, 0)
        return b''.join(b for _, b in written)

    def bash(self, command):
        return self.run_hook({'tool_name': 'Bash', 'tool_input': {'command': command}})

    def test_denies_default_heavy_commands_when_on(self):
        self.host('# Host\n\n## Heavy jobs\n\n- Heavy-job gate: on\n- Load limit: 25\n')
        for command in DENIED:
            with self.subTest(command=command):
                out = self.bash(command)
                self.assertEqual(out, hook.MESSAGE)
                decision = json.loads(out)['hookSpecificOutput']
                self.assertEqual(decision['permissionDecision'], 'deny')
                self.assertIn('heavy_run.py', decision['permissionDecisionReason'])
                self.assertNotIn(command, out.decode())

    def test_allows_wrapped_and_unclassified_forms(self):
        self.host('## Heavy jobs\nHeavy-job gate: on\n')
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command), b'')

    def test_configured_patterns_replace_the_default_list(self):
        self.host('## Heavy jobs\n- Heavy-job gate: on\n- Heavy command: pnpm test:e2e\n')
        self.assertEqual(self.bash('pnpm test:e2e --project web'), hook.MESSAGE)
        self.assertEqual(self.bash('/usr/local/bin/pnpm test:e2e'), hook.MESSAGE)
        self.assertEqual(self.bash('docker compose up'), b'')
        self.assertEqual(self.bash('python3 -I /abs/heavy_run.py run -- pnpm test:e2e'), b'')

    def test_allows_when_off_missing_or_unreadable(self):
        cases = {'gate off': '## Heavy jobs\n- Heavy-job gate: off\n',
                 'no gate line': '## Heavy jobs\n- Load limit: 25\n',
                 'other section': '## Other\n- Heavy-job gate: on\n## Heavy jobs\n'}
        for name, text in cases.items():
            with self.subTest(name):
                self.host(text)
                self.assertEqual(self.bash('docker compose up'), b'')
        (self.root / 'host.md').unlink()
        self.assertEqual(self.bash('docker compose up'), b'')
        self.host('## Heavy jobs\n- Heavy-job gate: on\n')
        (self.root / 'host.md').chmod(0)
        self.addCleanup((self.root / 'host.md').chmod, 0o600)
        self.assertEqual(self.bash('docker compose up'), b'')

    def test_allows_when_the_data_root_is_unsafe(self):
        self.host('## Heavy jobs\n- Heavy-job gate: on\n')
        self.root.chmod(0o777)
        self.addCleanup(self.root.chmod, 0o700)
        self.assertEqual(self.bash('docker compose up'), b'')

    def test_env_off_disables(self):
        self.host('## Heavy jobs\n- Heavy-job gate: on\n')
        for value in ('off', 'OFF', '0', 'false', 'no'):
            with self.subTest(value), mock.patch.dict(os.environ, {'FNL_HEAVY_GATE': value}):
                self.assertEqual(self.bash('docker compose up'), b'')

    def test_allows_malformed_input_and_other_tools(self):
        self.host('## Heavy jobs\n- Heavy-job gate: on\n')
        for raw in (b'', b'not json', b'[]', b'{"tool_name": "Bash"}', b'{"tool_name": "Bash", "tool_input": []}',
                    b'{"tool_name": "Bash", "tool_input": {"command": 7}}', b'\xff\xfe',
                    b'{"tool_name":"Bash","tool_input":{"command":"docker compose up"}}' + b' ' * hook.INPUT_LIMIT):
            with self.subTest(raw=raw[:40]):
                self.assertEqual(self.run_hook(None, raw=raw), b'')
        for tool in ('Write', 'Edit', 'Read', 'AskUserQuestion', 'bash'):
            with self.subTest(tool=tool):
                self.assertEqual(self.run_hook({'tool_name': tool, 'tool_input': {'command': 'docker compose up'}}), b'')

    def test_writes_no_file(self):
        self.host('## Heavy jobs\n- Heavy-job gate: on\n')
        before = sorted(p for p in self.home.rglob('*'))
        self.bash('docker compose up')
        self.bash('ls')
        self.assertEqual(sorted(p for p in self.home.rglob('*')), before)


class SetupTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = account(self, Path(temp.name) / 'home')
        self.root = self.home / '.finolabs/vibecode'
        self.root.mkdir(parents=True, mode=0o700)
        self.host = self.root / 'host.md'
        self.host.write_text('# Host\n\n## Heavy jobs\n\n- Load limit: 25\n\n## Other\nKeep: yes\n')
        self.claude = self.home / '.claude'
        self.claude.mkdir(mode=0o700)
        self.settings = self.claude / 'settings.json'
        self.other = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'other-hook'}]}
        self.settings.write_text(json.dumps({'model': 'x', 'hooks': {'PreToolUse': [self.other]}}))
        self.settings.chmod(0o600)
        # An installed copy outside any git work tree.
        self.plugin = self.home / "plugin with ' quote"
        (self.plugin / 'scripts').mkdir(parents=True)
        script = self.plugin / 'scripts' / setup.HOOK
        script.write_bytes((ROOT / 'scripts' / setup.HOOK).read_bytes())
        script.chmod(0o644)
        patch = mock.patch.object(setup, '__file__', str(self.plugin / 'skills/setup/scripts/heavy_gate_setup.py'))
        patch.start()
        self.addCleanup(patch.stop)
        env = mock.patch.dict(os.environ, {}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def preview(self, *args):
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['heavy_gate_setup.py', 'preview', *args]), contextlib.redirect_stdout(out):
            self.assertEqual(setup.main(), 0)
        return out.getvalue(), out.getvalue().rsplit('Digest: ', 1)[1].strip()

    def apply(self, value, yes=True):
        err = io.StringIO()
        argv = ['heavy_gate_setup.py', 'apply', '--digest', value] + (['--yes'] if yes else [])
        with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(err):
            return setup.main(), err.getvalue()

    def groups(self):
        return json.loads(self.settings.read_text()).get('hooks', {}).get('PreToolUse', [])

    def test_preview_is_a_dry_run(self):
        before = (self.settings.read_bytes(), self.host.read_bytes())
        text, value = self.preview('--on')
        self.assertRegex(value, r'^[0-9a-f]{64}$')
        self.assertIn('heavy_gate_hook.py', text)
        self.assertNotIn('other-hook', text)
        self.assertEqual((self.settings.read_bytes(), self.host.read_bytes()), before)
        self.assertEqual(list(self.claude.glob('settings.json.bak-*')), [])

    def test_on_then_remove(self):
        original = self.settings.read_bytes()
        _, value = self.preview('--on')
        self.assertEqual(self.apply(value)[0], 0)
        groups = self.groups()
        self.assertEqual(groups[0], self.other)
        self.assertEqual(len(groups), 2)
        command = groups[1]['hooks'][0]['command']
        script = shlex.quote(str(self.plugin / 'scripts' / setup.HOOK))
        self.assertEqual(command, f'[ -f {script} ] && python3 -I {script}; exit 0')
        self.assertEqual(groups[1]['matcher'], 'Bash')
        self.assertEqual(json.loads(self.settings.read_text())['model'], 'x')
        self.assertIn('## Heavy jobs\n\n- Heavy-job gate: on\n- Load limit: 25\n\n## Other\nKeep: yes\n', self.host.read_text())
        backups = list(self.claude.glob('settings.json.bak-*'))
        self.assertEqual([b.read_bytes() for b in backups], [original])
        # Installing again is idempotent: one gate group only.
        _, value = self.preview('--on')
        self.assertEqual(self.apply(value)[0], 0)
        self.assertEqual(len(self.groups()), 2)
        _, value = self.preview('--remove')
        self.assertEqual(self.apply(value)[0], 0)
        self.assertEqual(self.groups(), [self.other])
        self.assertIn('- Heavy-job gate: off\n', self.host.read_text())
        self.assertEqual(self.host.read_text().count('Heavy-job gate'), 1)

    def test_hook_command_allows_when_its_copy_is_gone(self):
        _, value = self.preview('--on')
        self.assertEqual(self.apply(value)[0], 0)
        command = self.groups()[1]['hooks'][0]['command']
        self.assertTrue(command.endswith('; exit 0'))
        (self.plugin / 'scripts' / setup.HOOK).unlink()
        # A removed copy (an older plugin version) allows: the shell form exits 0 with no output.
        import subprocess
        done = subprocess.run(['/bin/sh', '-c', command], input=b'{}', capture_output=True, timeout=10,
                              env={'PATH': '/usr/bin:/bin'})
        self.assertEqual((done.returncode, done.stdout), (0, b''))

    def test_missing_section_and_settings_are_created(self):
        self.host.write_text('# Host\n')
        self.settings.unlink()
        _, value = self.preview('--on')
        self.assertEqual(self.apply(value)[0], 0)
        self.assertEqual(self.host.read_text(), '# Host\n\n## Heavy jobs\n\n- Heavy-job gate: on\n')
        self.assertEqual(len(self.groups()), 1)
        self.assertEqual(stat.S_IMODE(self.settings.stat().st_mode), 0o600)

    def test_refusals(self):
        _, value = self.preview('--on')
        self.assertEqual(self.apply(value, yes=False)[0], 1)
        self.assertEqual(self.apply('0' * 64)[0], 1)
        self.settings.write_text('{}')
        code, err = self.apply(value)
        self.assertEqual(code, 1)
        self.assertIn('preview again', err)
        self.assertEqual(self.settings.read_text(), '{}')

    def test_git_work_tree_copy_is_refused(self):
        (self.plugin / '.git').mkdir()
        err = io.StringIO()
        with mock.patch.object(sys, 'argv', ['heavy_gate_setup.py', 'preview', '--on']), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(setup.main(), 1)
        self.assertIn('installed copy', err.getvalue())
        # Removal needs no script copy.
        self.preview('--remove')

    def test_duplicate_section_is_refused(self):
        self.host.write_text('## Heavy jobs\n\n## Heavy jobs\n')
        with mock.patch.object(sys, 'argv', ['heavy_gate_setup.py', 'preview', '--on']), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(setup.main(), 1)


if __name__ == '__main__':
    unittest.main()
