# delegate

Loaded by the agent when work is split across agents; you can also type it.

**What it does.** Hands work to other coding agents (Claude Code, Codex, Antigravity, ZCode) and runs it from whichever one you are in: grade, route, brief, dispatch, watch, accept and record each run in the ledger.

**When to use it.** Giving a task to another agent, choosing the agent and model for several tasks, running independent tasks in parallel, a quota running out, or a watched run that stalls or times out.

**Type:** Claude Code `/finolabs-vibecode:delegate` or `/delegate`; Codex `$delegate`; Antigravity `/delegate`.

## Tips

- `/setup mode` shows or changes Delegation mode; `/setup scan` refreshes which agents and models are present.
- Parallel runs go up to the limit you set per repository (3 by default).
- Accepting a run needs a passing check receipt for its current head (`checks`).
- For the brief of a single task, use `handoff`.
- Heavy jobs run one at a time through `heavy_run.py`, which waits while the one-minute load is at or above 25 by default; on Claude Code the opt-in heavy-job gate refuses a listed heavy command run without it (`FNL_HEAVY_GATE=off` for one session).
- Worktrees of finished runs are removed in the background once their branch merges, clean and pushed. `ledger.py clean-worktrees` runs it by hand with a report; `FNL_WORKTREE_CLEAN=manual` keeps only that, and `off` stops it.
- One-shot runs (reviews, advice, navigator runs, small tasks with no rework expected) save no session: `codex exec --ephemeral` and `claude -p --no-session-persistence`. A rework round after one is a new run whose brief carries the earlier findings and the diff.
- An accepted Codex run's saved session can be archived once its pull request merged: `ledger.py codex-threads --dispatch <id>` prints the `codex archive <id>` command. The ledger keeps only a digest of the session id (`codex_thread`). `codex unarchive` brings a session back; nothing deletes session files.
- Antigravity conversations from `agy -p` and the `agybird` desktop transport are `agybird`'s to archive.
