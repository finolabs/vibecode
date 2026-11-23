#!/usr/bin/env python3
"""Claude Code PreToolUse heavy-job gate (docs/specs/heavy-jobs.md part D); every failure allows silently, exit 0.

Opt-in: it acts only when `Heavy-job gate: on` is recorded under `## Heavy jobs` in the canonical host config. It
denies one Bash call only when a simple command in it is heavy (the section's `Heavy command:` patterns, else the
built-in list) and is not wrapped in the `heavy_run.py` launch form. The command text is matched in memory only:
never stored, logged, printed or sent. Anything it cannot classify with certainty is allowed.
"""

import os
import signal
import sys

MESSAGE = (b'{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny",'
           b'"permissionDecisionReason":"Heavy-job gate: this command is listed as heavy. Run it through heavy_run.py '
           b'(python3 -I <delegate skill folder>/scripts/heavy_run.py run --label <label> -- <command>) so heavy jobs '
           b'run one at a time on this machine."}}\n')
INPUT_LIMIT = 64 * 1024
PUNCTUATION = set(';&|()<>\n')
ASSIGNMENT = r'[A-Za-z_][A-Za-z0-9_]*='
PYTHON = {'python', 'python3'}
INTERPRETER_FLAGS = {'-I', '-B', '-E', '-s', '-S', '-u', '-IB', '-BI'}


class Uncertain(Exception):
    """The command cannot be classified with certainty; the gate allows it."""


def gate_on():
    """True only when the canonical host config records the gate on; any error means off."""
    sys.dont_write_bytecode = True
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import data_root
    text = data_root.read_data('host.md').decode('utf-8')
    on, patterns, in_section = False, [], False
    for line in text.splitlines():
        if line.startswith('## '):
            in_section = line.strip() == '## Heavy jobs'
            continue
        if not in_section:
            continue
        entry = line.strip()
        entry = entry[2:] if entry.startswith('- ') else entry
        if entry.startswith('Heavy-job gate:'):
            on = entry[len('Heavy-job gate:'):].strip() == 'on'
        elif entry.startswith('Heavy command:'):
            import shlex
            try:
                words = shlex.split(entry[len('Heavy command:'):])
            except ValueError:
                continue
            if words:
                patterns.append(words)
    return on, patterns


def simple_commands(command):
    """The simple commands of a shell command line, each a list of words; Uncertain when not plainly parseable."""
    import shlex
    if '`' in command or '$(' in command or '<(' in command or '>(' in command:
        raise Uncertain()
    lexer = shlex.shlex(command, posix=True, punctuation_chars=''.join(sorted(PUNCTUATION)))
    lexer.whitespace = ' \t\r'
    lexer.whitespace_split = True
    lexer.commenters = ''
    try:
        tokens = list(lexer)
    except ValueError:
        raise Uncertain() from None
    current, result = [], []
    for token in tokens:
        if set(token) <= PUNCTUATION:
            if '(' in token or ')' in token or token.startswith('<<'):
                raise Uncertain()
            if '<' not in token and '>' not in token:
                if current:  # `;`, `&`, `&&`, `|`, `||`, newlines and their runs end a simple command
                    result.append(current)
                current = []
                continue
            if ';' in token or '\n' in token or '&&' in token or '||' in token:
                raise Uncertain()
        current.append(token)  # a word, or a redirection kept as a word
    if current:
        result.append(current)
    return result


def base(word):
    return word.rsplit('/', 1)[-1]


def skip_assignments(words):
    import re
    index = 0
    while index < len(words) and re.match(ASSIGNMENT, words[index]):
        index += 1
    return words[index:]


def skip_interpreter(words, script):
    """Words after an optional `python3`/`python` with its flags, when the next word's base name is `script`."""
    if words and base(words[0]) in PYTHON:
        index = 1
        while index < len(words) and words[index] in INTERPRETER_FLAGS:
            index += 1
        if index < len(words) and base(words[index]) == script:
            return words[index + 1:]
        return None
    if words and base(words[0]) == script:
        return words[1:]
    return None


def wrapped(words):
    """True for the `heavy_run.py run` launch form, with an optional outer `run_env.py --`."""
    rest = skip_interpreter(words, 'run_env.py')
    if rest is not None:
        if rest[:1] == ['--']:
            rest = rest[1:]
        words = skip_assignments(rest)
    rest = skip_interpreter(words, 'heavy_run.py')
    return rest is not None and rest[:1] == ['run']


def default_heavy(words):
    name = base(words[0])
    args = words[1:]
    if name == 'docker-compose':
        return True
    if name == 'docker':
        return bool(args) and args[0] in {'run', 'build', 'compose', 'buildx'}
    if name == 'npx':
        return default_heavy(args) if args else False
    if name == 'pnpm':
        return args[:1] == ['exec'] and len(args) > 1 and default_heavy(args[1:])
    if name == 'playwright':
        return args[:1] == ['test']
    if name == 'go':
        return args[:1] == ['test'] and any('contract' in arg or 'integration' in arg for arg in args[1:])
    if name in PYTHON or (name.startswith('python3.') and name[8:].isdigit()):
        index = 0
        while index < len(args) and args[index] in INTERPRETER_FLAGS:
            index += 1
        if args[index:index + 2] != ['-m', 'unittest']:
            return False
        rest, modules, index = args[index + 2:], [], 0
        while index < len(rest):
            word = rest[index]
            if word in ('-k', '-p', '-s', '-t'):
                index += 2
                continue
            if not word.startswith('-'):
                modules.append(word)
            index += 1
        return not modules or modules[0] == 'discover' or len(modules) > 2
    return False


def heavy(words, patterns):
    if not words:
        return False
    if patterns:
        for pattern in patterns:
            if len(words) >= len(pattern) and base(words[0]) == base(pattern[0]) and words[1:len(pattern)] == pattern[1:]:
                return True
        return False
    return default_heavy(words)


def decide(command, patterns):
    """True when the gate denies `command`."""
    for words in simple_commands(command):
        words = skip_assignments(words)
        if words and base(words[0]) == 'env':
            raise Uncertain()
        if not words or wrapped(words):
            continue
        if heavy(words, patterns):
            return True
    return False


def main():
    try:
        signal.signal(signal.SIGALRM, lambda *_: os._exit(0))
        signal.alarm(2)
        if os.environ.get('FNL_HEAVY_GATE', '').lower() in {'off', '0', 'false', 'no'}:
            return 0

        import json

        raw = sys.stdin.buffer.read(INPUT_LIMIT)
        if len(raw) == INPUT_LIMIT:
            return 0
        event = json.loads(raw)
        if not isinstance(event, dict) or event.get('tool_name') != 'Bash':
            return 0
        tool_input = event.get('tool_input')
        command = tool_input.get('command') if isinstance(tool_input, dict) else None
        if not isinstance(command, str) or not command.strip():
            return 0
        on, patterns = gate_on()
        if on and decide(command, patterns):
            # Claude Code's documented PreToolUse JSON decision, with exit 0.
            os.write(1, MESSAGE)
    except Exception:
        pass
    finally:
        try:
            signal.alarm(0)
        except Exception:
            pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
