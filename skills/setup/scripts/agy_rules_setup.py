#!/usr/bin/env python3
"""Preview and add the Antigravity allow-rules a reviewer needs, from a closed list, one rule per chosen item.

`preview --rule <name> [--rule <name> ...]` stores a private plan and prints only the rules it adds or the count it
removes, never another rule; `apply --digest <hex> --yes` writes it after a backup. The rules are prefix rules of
read-only git commands and this install's `post_review.py`; adding `posting` also removes the `post_review.py` rules
that point to no script of this install. Owner decision, 28/11/2026: setup offers them when it sets Antigravity up as
a reviewer, with this preview, a backup and a yes per item."""
from contextlib import ExitStack
try:
    import fcntl
except ImportError:
    raise ImportError("finolabs-vibecode needs POSIX file APIs (pwd, fcntl) and supports macOS and Linux; on Windows run it under WSL.") from None
import json
import os
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import compact_setup as cs
import data_root as dr

STATE = 'state/agy-rules-setup'
GIT = ('show', 'diff', 'log', 'rev-parse', 'merge-base', 'ls-files', 'blame', 'grep')
POSTING_PATH = re.compile(r"/[^\s()'\"]*post_review\.py")


def posting_scripts():
    """This install's `post_review.py` copies, resolved; the first is the one a new rule names."""
    root = Path(__file__).resolve().parents[3]
    found = [root / 'skills/review-gate/scripts/post_review.py', root / 'scripts/post_review.py']
    return [str(path.resolve()) for path in found if path.is_file()]


def posting_rule():
    scripts = posting_scripts()
    if not scripts or not re.fullmatch(r"/[A-Za-z0-9._/-]+", scripts[0]):
        raise cs.Refusal('no post_review.py of this install with a plain path')
    return 'command(python3 -I ' + scripts[0] + ')'


def rules():
    found = {'git-' + name: f'command(git {name})' for name in GIT}
    try:
        found['posting'] = posting_rule()
    except cs.Refusal:
        pass
    return found


RULES = rules()


def backup_name(folder, name):
    base = name + '.bak-' + time.strftime('%Y%m%d-%H%M%S')
    number = 1
    while True:
        candidate = base + f'-{number}'
        try:
            os.lstat(candidate, dir_fd=folder)
        except FileNotFoundError:
            return candidate
        number += 1


def settings_path():
    return dr.account_home() / '.gemini/antigravity-cli/settings.json'


def stale(rule):
    """A rule naming `post_review.py` that resolves to no script of this install."""
    current = set(posting_scripts())
    return 'post_review.py' in rule and not any(os.path.realpath(p) in current for p in POSTING_PATH.findall(rule))


def change(raw, names):
    """The new file bytes, the rules added and the count of stale posting rules removed; other keys are kept."""
    data = {} if raw is None else json.loads(raw.decode('utf-8'))
    if not isinstance(data, dict):
        raise cs.Refusal('settings are not a JSON object')
    permissions = data.setdefault('permissions', {})
    if not isinstance(permissions, dict):
        raise cs.Refusal('permissions is not an object')
    allow = permissions.setdefault('allow', [])
    if not isinstance(allow, list) or not all(isinstance(rule, str) for rule in allow):
        raise cs.Refusal('permissions.allow is not a list of rules')
    removed = [rule for rule in allow if stale(rule)] if 'posting' in names else []
    kept = [rule for rule in allow if rule not in removed]
    added = [RULES[name] for name in names if RULES[name] not in kept]
    permissions['allow'] = kept + added
    if not added and not removed:
        return raw, added, 0, len(kept)
    return (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8'), added, len(removed), len(kept)


def validate(names):
    if not names or len(set(names)) != len(names) or any(name not in RULES for name in names):
        raise cs.Refusal('choose rules from the closed list, each once')


def preview(names):
    validate(names)
    path = settings_path()
    with dr.relocated_folder(path.parent) as folder:
        raw, mode = cs.read_target(folder, path.name)
        backup = backup_name(folder, path.name)
    new, added, removed, kept = change(raw, names)
    plan = {'names': names, 'rules': [RULES[name] for name in names], 'created': time.time(), 'path': str(path),
            'sha256': cs.content_hash(raw), 'mode': mode, 'backup': backup}
    value = cs.digest(plan)
    with dr.data_folder(STATE, create=True, private=True) as state:
        dr.atomic_write(state, 'preview.json', json.dumps({'plan': plan, 'digest': value}).encode())
    print('Target: ' + str(path))
    for rule in added:
        print('Add: ' + rule)
    if removed:
        print(f"Remove: {removed} post_review.py {'rule that points' if removed == 1 else 'rules that point'} "
              'to no script of this install')
    print(f'Other allow-rules (unchanged): {kept - sum(1 for r in plan["rules"] if r not in added)}')
    if new == raw:
        print('No change.')
    else:
        print('The file is written back as JSON with two-space indents; every other key is kept.')
        if any(name.startswith('git-') for name in names):
            print('Prefix rules allow the command with any arguments: `git diff --output=<file>` and '
                  '`git log --output=<file>` can write a file.')
        if 'posting' in names:
            print('The posting rule runs the named post_review.py with any arguments; it posts only through gh pr comment.')
        print('Backup: ' + str(path.parent / backup) if raw is not None else 'Backup: none (new file)')
    print('Digest: ' + value)


def apply(value, yes):
    if not yes or not isinstance(value, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', value):
        raise cs.Refusal('clear yes and full 64-hex preview digest required')
    value = value.lower()
    with ExitStack() as stack:
        state = stack.enter_context(dr.data_folder(STATE, private=True))
        fcntl.flock(state, fcntl.LOCK_EX | fcntl.LOCK_NB)
        saved = json.loads(cs.read_plan(state))
        if (not isinstance(saved, dict) or set(saved) != {'plan', 'digest'}
                or saved['digest'] != value or cs.digest(saved['plan']) != value):
            raise cs.Refusal('digest mismatch; preview again')
        plan = saved['plan']
        if not isinstance(plan, dict) or set(plan) != {'names', 'rules', 'created', 'path', 'sha256', 'mode', 'backup'}:
            raise cs.Refusal('invalid plan')
        validate(plan['names'])
        if plan['rules'] != [RULES[name] for name in plan['names']]:
            raise cs.Refusal('rules changed; preview again')
        if type(plan['created']) not in (int, float) or not 0 <= time.time() - plan['created'] <= 3600:
            raise cs.Refusal('preview expired; preview again')
        path = settings_path()
        if plan['path'] != str(path):
            raise cs.Refusal('invalid target path; preview again')
        folder = stack.enter_context(dr.relocated_folder(path.parent))
        raw, mode = cs.read_target(folder, path.name)
        if cs.content_hash(raw) != plan['sha256'] or mode != plan['mode']:
            raise cs.Refusal('target changed; preview again')
        if not re.fullmatch(re.escape(path.name) + r'\.bak-[0-9]{8}-[0-9]{6}-[1-9][0-9]*', plan['backup']):
            raise cs.Refusal('invalid backup name')
        new = change(raw, plan['names'])[0]
        if new != raw:
            if raw is not None:
                fd = os.open(plan['backup'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=folder)
                with os.fdopen(fd, 'wb') as stream:
                    os.fchmod(stream.fileno(), mode & 0o600)
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            cs.write_target(folder, path.name, new, mode & 0o600)
        os.unlink('preview.json', dir_fd=state)
        os.fsync(state)
    print('Antigravity allow-rules saved.' if new != raw else 'No change.')


def main():
    try:
        parser = cs.Parser(description=__doc__)
        commands = parser.add_subparsers(dest='action', required=True)
        pre = commands.add_parser('preview')
        pre.add_argument('--rule', action='append', required=True)
        app = commands.add_parser('apply')
        app.add_argument('--digest', required=True)
        app.add_argument('--yes', action='store_true')
        args = parser.parse_args()
        if args.action == 'preview':
            preview(args.rule)
        else:
            apply(args.digest, args.yes)
        return 0
    except cs.Refusal as error:
        print('Antigravity rule setup refused: ' + str(error), file=sys.stderr)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        print('Antigravity rule setup refused: unsafe, unreadable or invalid file or plan', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
