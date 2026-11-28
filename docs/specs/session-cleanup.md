# Session cleanup: less clutter from delegated runs
Status: in progress; owner decisions of 2026-11-28 (all four parts approved); pull request pending.

## Why

Delegation leaves a saved session behind for every run. On the owner's machine on 2026-11-28 there were 472 project folders of headless `claude -p` runs under one Claude Code config folder and 314 Codex session files, most of them one-shot reviews, advisor and navigator runs nobody resumes. Coordinators also open desktop child sessions that stay in the sidebar after their pull request merged, and Antigravity keeps a conversation for every `agy -p` and desktop transport run. Each saved session costs disk space, and every one left in a session picker or sidebar makes the live ones harder to find.

## Goal and acceptance

- [ ] AC1 A one-shot run (review, advisor, navigator, a small task without expected rework) is dispatched without a saved session by default: `codex exec --ephemeral` and `claude -p --no-session-persistence` (any Claude Code install, the extra ones included). A task that expects rework rounds keeps its session. Checked in `delegate` `references/agents/codex.md`, `claude-code.md`, `host-template.md`, `loop.md`, `budget-and-liveness.md` and the review command shapes in `review-gate` references.
- [ ] AC2 A rework round after an ephemeral run is a new run whose brief carries the earlier findings and the diff; nothing tells the coordinator to resume a run that was ephemeral.
- [ ] AC3 `tidy` (its archiving section and [`titles.md`](../../skills/tidy/references/titles.md) "Archiving") and `delegate`'s session-per-task notes say: a coordinator that opens a desktop session with `start_session` for a task ending in a pull request has that session turn on its PR monitor's `auto_archive_on_close` (the switch acts only on the calling session), and archives a linked session that is idle and whose pull request merged, after turning Remote Control off. Marked advisory.
- [ ] AC4 `ledger.py finish` of a Codex dispatch whose `--log-path` log names exactly one Codex session id stores `codex_thread`, the first 16 hex digits of the SHA-256 of that id, never the id itself; any other log stores nothing new.
- [ ] AC5 `ledger.py codex-threads` lists, for this repository's accepted Codex dispatches that carry `codex_thread`, the `codex archive <id>` command of each saved session it finds by file name, and says how many it did not find; it reads only file names, writes nothing and runs nothing.
- [ ] AC6 `delegate`'s Antigravity notes say that conversations made by `agy -p` and by the agybird desktop transport are agybird's to archive; vibecode only reports that the run finished.
- [ ] AC7 `PRIVACY.md`, `skills/delegate/references/ledger.md`, help pages, README and `CHANGELOG.md` describe the new field and command; no transcript file is deleted anywhere.

## Decisions (owner, 2026-11-28)

1. **All four parts.** The owner approved the four parts proposed in the coordinator session ("Làm hết đi").
2. **Ephemeral by default for one-shot runs.** Reviews, advisor and navigator runs and small tasks run without a saved session; tasks that expect rework rounds keep one. A rework after an ephemeral run starts a new run that carries the findings and the diff.
3. **Desktop child sessions archive themselves.** Through the PR monitor's `auto_archive_on_close`, plus archiving idle linked sessions whose pull request merged.
4. **Ledger digest for Codex threads.** The owner accepted the privacy and schema change: the ledger records a digest of the Codex session id, following `checkout_instance`, so a finished run's session can be found without storing an id or a path.
5. **Antigravity is agybird's.** The coordinator sends agybird a feature request separately; vibecode documents the boundary only.
6. **Never delete transcripts.** `~/.codex/sessions` and Claude Code's `projects` folders are never deleted by the plugin or by an instruction in it: deletion cannot be undone and breaks resume. Archiving moves a Codex session to `archived_sessions`, and `codex unarchive` brings it back.

## Plan

### Part 1: ephemeral one-shot runs

Checked on 2026-11-28 against the installed CLIs: `codex exec --help` (codex-cli 0.169.0) lists `--ephemeral` ("Run without persisting session files to disk"); `claude --help` lists `--no-session-persistence` ("Don't save sessions to disk; they can't be resumed (only works with --print)"). Neither is a script change: the command shapes in the agent notes, the host template and the review references gain the flag for one-shot runs. An ephemeral Codex run still prints `session id:` in its header, but no file is saved, so nothing can resume it. `codex review` has no `--ephemeral` flag in 0.169.0, but `codex exec review` takes it, so Codex's own review flow runs as `codex exec review --ephemeral --base <branch>`.

Rework: `loop.md` and `budget-and-liveness.md` already prefer a new run with a short follow-up brief over resuming; the text now says that after an ephemeral run this is the only way, and the brief carries the earlier findings and the diff (or the head to diff against).

### Part 2: desktop child sessions

No script can call the desktop app's tools, so this is advisory text in `tidy` and `delegate`. When a coordinator opens a session with `start_session` for a task whose result is a pull request, the session's brief tells it to call the PR tools' `set_monitor` with `auto_archive_on_close: true` once it has bound its pull request. Checked on 2026-11-28 in the tool's schema: the switch acts only on the calling session's own bound pull request ("archive this session once the PR merges or closes"), so the coordinator cannot set it for another session. When a linked session is idle and its pull request merged, the coordinator turns Remote Control off (`set_remote_control` with `enabled: false`) and archives it (`archive_session`). Archiving is reversible (`unarchive_session`); deleting a session is not part of this.

### Part 3: persistent Codex sessions

Checked on 2026-11-28 (codex-cli 0.169.0): `codex archive <SESSION>` archives a saved session by id or name, `codex unarchive` restores it, and the app-server protocol (`codex app-server generate-json-schema`) has `thread/archive` with a single `threadId` parameter. Saved sessions are files named `rollout-<time>-<id>.jsonl` under `sessions/YYYY/MM/DD/` of the Codex home, and archived ones move to `archived_sessions/`. A `codex exec` log starts with a header line `session id: <id>`; with `--json` the first event is `thread.started` with `thread_id`.

The plugin runs no Codex program for this: the CLI command needs no new scoped exception, and the coordinator runs it as any other command it runs.

- `finish`: `ledger.py finish` already reads the whole log through the descriptor-checked scan when `--log-path` is given. For a dispatch whose start record has `agent: codex`, it looks in that text for the session id (a `session id: <id>` line or a `thread.started` event's `thread_id`, each a UUID). When exactly one distinct id is found, the finish line gets `codex_thread`: the first 16 hex digits of the SHA-256 of the lowercase id. No id, two different ids, an unscanned log or another agent store nothing. The id is never stored, printed or logged.
- `codex-threads`: a new read-only subcommand. It takes this repository's accepted Codex dispatches that carry `codex_thread` (the same project resolution as `stale`; `--dispatch <id>` narrows it to named dispatches), lists the file names in the Codex home's `sessions/YYYY/MM/DD/` folders from the day before each dispatch's start to the day after its finish (no link followed, only regular files whose name matches the rollout pattern), hashes the id in each name and matches. It prints `codex archive <id>  # <dispatch id> <project>: <task>` per match and one line counting dispatches with no saved session (already archived, an ephemeral run, or a session file gone). It writes nothing, runs nothing and reads no file content. The Codex home is `CODEX_HOME` when set, else `.codex` in the account home, as the compaction nudge resolves it.
- Merged: archiving waits for the pull request to merge. The command cannot see a forge, so this stays agent judgment (advisory): the coordinator runs `codex-threads --dispatch <id>` after it saw the merge, and runs each printed command.
- A predictable id could be guessed from its digest, as with `coord_session`: the ledger stays private.

### Part 4: Antigravity

`agy -p` and the agybird desktop transport create Antigravity conversations that only agybird knows how to find. `delegate`'s Antigravity notes say these are agybird's to archive and that vibecode reports only that the run finished; the coordinator sends the feature request to agybird separately.

## Tasks

### US1 Ephemeral runs
- [ ] T1 Command shapes with `--ephemeral` and `--no-session-persistence` in `agents/codex.md`, `agents/claude-code.md`, `host-template.md` and the review references
- [ ] T2 Rework after an ephemeral run in `loop.md` and `budget-and-liveness.md`

### US2 Desktop sessions
- [ ] T3 `tidy` archiving text and [`titles.md`](../../skills/tidy/references/titles.md); `delegate` session-per-task notes

### US3 Codex threads
- [ ] T4 Red tests for `codex_thread` and `codex-threads`
- [ ] T5 `ledger.py` field and subcommand
- [ ] T6 `ledger.md`, `PRIVACY.md`

### US4 Antigravity
- [ ] T7 Boundary in `agents/antigravity.md`

### Docs
- [ ] T8 Help pages, README, CHANGELOG

## Evidence

Pending.
