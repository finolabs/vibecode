#!/usr/bin/env python3
"""Preview, apply or remove the opt-in heavy-job gate on Claude Code (docs/specs/heavy-jobs.md part D).

`preview --on` or `preview --remove` shows the change and stores a plan with a digest; nothing is written (the dry
run). `apply --digest <hex> --yes` writes it: `Heavy-job gate: on|off` under `## Heavy jobs` in the canonical host
config, and the gate's own `PreToolUse` group for `Bash` in the user's Claude Code settings (added for on, removed
for off), keeping a backup of a settings file it changes. Every other key and hook group stays as it was.
"""
from contextlib import ExitStack
import difflib
try:
    import fcntl
except ImportError:
    raise ImportError("finolabs-vibecode needs POSIX file APIs (pwd, fcntl) and supports macOS and Linux; on Windows run it under WSL.") from None
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import compact_setup as common
import data_root as dr

Refusal = common.Refusal
STATE = 'state/heavy-gate-setup'
HOOK = 'heavy_gate_hook.py'
SECTION = '## Heavy jobs'
LINE = re.compile(r'^(?:- )?Heavy-job gate:.*$')


def hook_command():
    """The hook command for this installed copy; the folder must be owner-checked and outside any git work tree."""
    root = Path(os.path.abspath(__file__)).parents[3]  # not resolved: a symlinked folder must be seen
    try:
        with dr.relocated_folder(root / 'scripts') as folder:
            info = os.stat(HOOK, dir_fd=folder, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
                raise Refusal('the gate script is not a private regular file')
    except FileNotFoundError:
        raise Refusal('install the whole finolabs-vibecode plugin') from None
    except ValueError as error:
        if isinstance(error, Refusal):
            raise
        raise Refusal('plugin folder is unsafe or inside a git work tree; use the installed copy of the plugin') from None
    quoted = shlex.quote(str(root / 'scripts' / HOOK))
    # A missing script (an older plugin copy removed after an update) allows: the command always exits 0.
    return f'[ -f {quoted} ] && python3 -I {quoted}; exit 0'


def group(command):
    return {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command, 'timeout': 5}]}


def ours(entry):
    """True for a hook group that runs only this gate, from any installed copy."""
    if not isinstance(entry, dict) or not isinstance(entry.get('hooks'), list) or not entry['hooks']:
        return False
    return all(isinstance(hook, dict) and isinstance(hook.get('command'), str)
               and ('/scripts/' + HOOK) in hook['command'] for hook in entry['hooks'])


def settings_change(raw, command):
    """Settings with every gate group removed from `hooks.PreToolUse`, then this one added when `command` is set."""
    data = json.loads(raw, object_pairs_hook=common.json_object, parse_float=common.json_float,
                      parse_constant=common.json_constant) if raw is not None else {}
    if not isinstance(data, dict):
        raise Refusal('settings must be a JSON object')
    hooks = data.get('hooks', {})
    if not isinstance(hooks, dict):
        raise Refusal('hooks must be a JSON object')
    groups = hooks.get('PreToolUse', [])
    if not isinstance(groups, list):
        raise Refusal('hooks.PreToolUse must be a list')
    updated = [entry for entry in groups if not ours(entry)]
    if command is not None:
        updated.append(group(command))
    if updated == groups:
        return raw
    hooks = dict(hooks)
    if updated:
        hooks['PreToolUse'] = updated
    else:
        hooks.pop('PreToolUse', None)
    data = dict(data)
    if hooks:
        data['hooks'] = hooks
    else:
        data.pop('hooks', None)
    return (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def host_change(raw, on):
    """host.md with one `- Heavy-job gate: on|off` line in `## Heavy jobs`, the section added when missing."""
    text = raw.decode('utf-8') if raw is not None else ''
    newline = '\r\n' if '\r\n' in text else '\n'
    lines = text.splitlines(keepends=True)
    value = '- Heavy-job gate: ' + ('on' if on else 'off') + newline
    fence, start, end = None, None, len(lines)
    for index, line in enumerate(lines):
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None and re.match(r'^#{1,2} ', line):
            if line.strip() == SECTION:
                if start is not None:
                    raise Refusal('duplicate heavy jobs section')
                start = index
            elif start is not None and end == len(lines):
                end = index
    if start is None:
        separator = ''
        if text and not text.endswith(newline * 2):
            separator = newline if text.endswith(newline) else newline * 2
        result = text + separator + SECTION + newline + newline + value
    else:
        body = lines[start + 1:end]
        found = [i for i, line in enumerate(body) if LINE.match(line.rstrip('\r\n'))]
        if len(found) > 1:
            raise Refusal('duplicate heavy-job gate line')
        if found:
            body[found[0]] = value
        else:
            at = 1 if body and not body[0].strip() else 0
            body.insert(at, value)
            if at == 0:
                body.insert(0, newline)
        result = ''.join(lines[:start + 1] + body + lines[end:])
    if len(result.encode()) > 262144:
        raise Refusal('host file too large')
    return result.encode()


def settings_path(folder):
    return common.checked_path(str(Path(folder or dr.account_home() / '.claude') / 'settings.json'), 'claude')


def read_host():
    try:
        with dr.root_folder() as folder:
            return common.read_target(folder, 'host.md')
    except FileNotFoundError:
        return None, 0o600


def checked_root():
    root = dr.consent_root()
    if root is None:
        raise Refusal('invalid data root')
    return root


def preview(on, folder=None):
    root = checked_root()
    command = hook_command() if on else None  # removal needs no script, so a missing copy cannot block it
    path = settings_path(folder)
    with dr.relocated_folder(path.parent) as target:
        raw, mode = common.read_target(target, path.name)
        backup = common.backup_name(target, path.name)
    old_host, host_mode = read_host()
    new_host = host_change(old_host, on)
    new_settings = settings_change(raw, command)
    plan = {'on': on, 'created': time.time(), 'root': str(root), 'path': str(path), 'sha256': common.content_hash(raw),
            'mode': mode, 'backup': backup, 'host_sha256': common.content_hash(old_host), 'host_mode': host_mode,
            'command': command}
    value = common.digest(plan)
    with dr.data_folder(STATE, create=True, private=True) as state:
        dr.atomic_write(state, 'preview.json', json.dumps({'plan': plan, 'digest': value}).encode())
    # Show only the gate's own group: other settings may hold secrets.
    print('Target: ' + str(path) + '\nExists: ' + ('yes' if raw is not None else 'no'))
    print('PreToolUse group (Bash): ' + ('add ' + json.dumps(group(command), ensure_ascii=True) if on else 'remove'))
    print('Change: ' + ('none' if new_settings == raw else 'yes'))
    print('Backup: ' + str(path.parent / backup) + (' (not needed)' if raw is None or new_settings == raw else ''))
    print('Target: ' + str(root / 'host.md'))
    if new_host == old_host:
        print('No difference.')
    else:
        print(''.join(difflib.unified_diff((old_host or b'').decode().splitlines(keepends=True),
                                           new_host.decode().splitlines(keepends=True),
                                           fromfile='before', tofile='after', n=0)), end='\n')
    print('With the gate on, Claude Code refuses a Bash call whose command is listed as heavy and not run through '
          'heavy_run.py. It reads the command in memory only, never stores or sends it, and allows on any error. '
          'FNL_HEAVY_GATE=off turns it off for a session; Codex and Antigravity are not covered.')
    print('Digest: ' + value)


def apply(value, yes):
    if not yes or not isinstance(value, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', value):
        raise Refusal('clear yes and full 64-hex preview digest required')
    value = value.lower()
    with ExitStack() as stack:
        state = stack.enter_context(dr.data_folder(STATE, private=True))
        fcntl.flock(state, fcntl.LOCK_EX | fcntl.LOCK_NB)
        saved = json.loads(common.read_plan(state), object_pairs_hook=common.json_object,
                           parse_float=common.json_float, parse_constant=common.json_constant)
        if (not isinstance(saved, dict) or set(saved) != {'plan', 'digest'}
                or saved['digest'] != value or common.digest(saved['plan']) != value):
            raise Refusal('digest mismatch; preview again')
        plan = saved['plan']
        if (not isinstance(plan, dict) or set(plan) != {'on', 'created', 'root', 'path', 'sha256', 'mode', 'backup',
                                                         'host_sha256', 'host_mode', 'command'}
                or type(plan['on']) is not bool):
            raise Refusal('invalid plan')
        if plan['root'] != str(checked_root()) or plan['command'] != (hook_command() if plan['on'] else None):
            raise Refusal('root or command changed; preview again')
        if type(plan['created']) not in (int, float) or not 0 <= time.time() - plan['created'] <= 3600:
            raise Refusal('preview expired; preview again')
        path = common.checked_path(plan['path'], 'claude')
        if (not isinstance(plan['backup'], str)
                or not re.fullmatch(r'settings\.json\.bak-\d{8}(?:-[1-9][0-9]*)?', plan['backup'])):
            raise Refusal('invalid backup name')
        target = stack.enter_context(dr.relocated_folder(path.parent))
        host_folder = stack.enter_context(dr.root_folder(create=True))
        fcntl.flock(host_folder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raw, mode = common.read_target(target, path.name)
        old_host, host_mode = common.read_target(host_folder, 'host.md')
        if (common.content_hash(raw) != plan['sha256'] or mode != plan['mode']
                or common.content_hash(old_host) != plan['host_sha256'] or host_mode != plan['host_mode']):
            raise Refusal('target changed; preview again')
        new_host = host_change(old_host, plan['on'])
        new_settings = settings_change(raw, plan['command'])
        if raw is not None and new_settings != raw:
            # Exclusive creation refuses an existing backup before anything changes.
            fd = os.open(plan['backup'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=target)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        # host.md first: a failed settings write then leaves the gate recorded but not installed, which allows.
        if new_host != old_host:
            common.write_target(host_folder, 'host.md', new_host, host_mode)
        if new_settings != raw:
            common.write_target(target, path.name, new_settings, mode if raw is not None else 0o600)
            print('Updated: ' + str(path))
        os.unlink('preview.json', dir_fd=state)
        os.fsync(state)
    print('Heavy-job gate ' + ('on.' if plan['on'] else 'off.'))


def main():
    try:
        parser = common.Parser(description=__doc__)
        commands = parser.add_subparsers(dest='action', required=True)
        pre = commands.add_parser('preview')
        pre.add_argument('--folder')
        choice = pre.add_mutually_exclusive_group(required=True)
        choice.add_argument('--on', action='store_true')
        choice.add_argument('--remove', action='store_true')
        app = commands.add_parser('apply')
        app.add_argument('--digest', required=True)
        app.add_argument('--yes', action='store_true')
        args = parser.parse_args()
        if args.action == 'preview':
            preview(args.on, args.folder)
        else:
            apply(args.digest, args.yes)
        return 0
    except Refusal as error:
        print('Heavy-job gate setup refused: ' + str(error), file=sys.stderr)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        print('Heavy-job gate setup refused: unsafe, unreadable or invalid file or plan', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
