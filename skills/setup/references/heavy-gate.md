# Heavy-job gate (Claude Code only)

Offered from `setup delegation` as its own consent; design in the plugin's heavy-jobs spec, part D.

First run `python3 -I <this skill folder>/scripts/heavy_gate_setup.py preview --on [--folder <config folder>]...` and the same with `--remove` instead of `--on` (default `~/.claude`; name each config folder the user runs Claude Code with, such as a `CLAUDE_CONFIG_DIR`, at most four, the same in both). Each is a dry run that writes only its private plan. Show both outputs, the Yes change and the No change with their `Digest:` lines, then ask:
"Turn on the heavy-job gate, which stops a heavy command in Claude Code unless it runs through heavy_run.py?"
Yes: Record Heavy-job gate: on in local host.md and add the gate's own Bash hook group to each Claude Code settings file shown, with a settings backup. It reads each Bash command in memory only, never stores or sends it, and allows on any error.
No: Record Heavy-job gate: off in local host.md and take out a gate group an earlier yes added, as the No change shows; nothing else changes; ask later.
Undo: Approve the `--remove` preview, or turn it off for a session with FNL_HEAVY_GATE=off.
Choices: "Yes, turn on the gate" / "No, leave it off".
After the answer, run `heavy_gate_setup.py apply --digest <full digest of that answer's preview> --yes`; a skipped or unclear answer applies neither.
Heavy commands are the `- Heavy command: <words>` lines under `## Heavy jobs`, else the built-in list (`docker run|build|compose|buildx`, `docker-compose`, `playwright test`, `go test` of contract or integration packages, `unittest` with no, `discover` or more than two modules).
After a plugin update, run the preview and apply again so the hook points at the new installed copy; until then an old copy that was removed simply allows.
Enforcer: the installer checks the stored private preview, full digest, 60-minute expiry, unchanged files and an owner-checked installed copy outside any git work tree; the gate (`scripts/heavy_gate_hook.py`) denies with one fixed message and allows on every error. Asking and showing the preview are advisory (agent judgment). Codex and Antigravity are not covered.
