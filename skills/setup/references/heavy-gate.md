# Heavy-job gate (Claude Code only)

Offered from `setup add delegation` as its own consent; design in the plugin's heavy-jobs spec, part D.

First run `python3 -I <this skill folder>/scripts/heavy_gate_setup.py preview --on` (a dry run: it writes nothing but its private plan) and show its output, then ask:
"Turn on the heavy-job gate, which stops a heavy command in Claude Code unless it runs through heavy_run.py?"
Yes: Record Heavy-job gate: on in local host.md and add the gate's own Bash hook group to your Claude Code settings, with a settings backup. It reads each Bash command in memory only, never stores or sends it, and allows on any error.
No: Record Heavy-job gate: off and leave your Claude Code settings unchanged; ask later.
Undo: Approve `preview --remove`, or turn it off for a session with FNL_HEAVY_GATE=off.
Choices: "Yes, turn on the gate" / "No, leave it off".
Only after that yes run `heavy_gate_setup.py apply --digest <full digest> --yes`.
After No, record off with `preview --remove` and its `apply` after the same answer; it also takes out a gate group an earlier yes added.
Heavy commands are the `- Heavy command: <words>` lines under `## Heavy jobs`, else the built-in list (`docker run|build|compose|buildx`, `docker-compose`, `playwright test`, `go test` of contract or integration packages, `unittest` with no, `discover` or more than two modules).
After a plugin update, run the preview and apply again so the hook points at the new installed copy; until then an old copy that was removed simply allows.
Enforcer: the installer checks the stored private preview, full digest, 60-minute expiry, unchanged files and an owner-checked installed copy outside any git work tree; the gate (`scripts/heavy_gate_hook.py`) denies with one fixed message and allows on every error. Asking and showing the preview are advisory (agent judgment). Codex and Antigravity are not covered.
