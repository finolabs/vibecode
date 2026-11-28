# Antigravity through the agybird desktop transport

Status: implemented; owner decisions 28/11/2026; for 0.3.5. The desktop envelope, the `deferred` outcome, the machine-wide Antigravity slot and the `desktop` review form have local tests; a live delegate run and a reviewer posting its own markers from the app (decision 6's pilot) remain unverified.

This document changes how [agent-roles.md](agent-roles.md), [parallel-instances.md](parallel-instances.md) and the `delegate` Antigravity page describe Antigravity. Where they disagree, this document wins from 0.3.5.

## Why

On 24/11/2026 the owner removed Antigravity from the roles and workers of his own host config, because driving it headless with `agy -p` raised a policy concern. agybird ([finolabs/agybird](https://github.com/finolabs/agybird), MIT) 0.4.8 adds an opt-in macOS desktop transport: it drives the signed-in Antigravity app through the macOS Accessibility API (JXA under `osascript`), one run at a time per machine (`~/.agybird/desktop.lock`), and returns the same envelope as its CLI runner with `evidence.transport: "desktop"`. That removes the headless use and brings Antigravity back as a worker and a reviewer.

Facts from agybird 0.4.8 (its README "Desktop transport" and `PRIVACY.md`):
- Opt-in: `/agybird:setup` (`setup --transport desktop`, or `--here` for one repository) or `--via desktop` for one call on `rescue`, `review` and `adversarial-review`.
- Preflight refusals and waits return `status: blocked` with `evidence.blocked_reason`: `not_macos`, `app_missing` (app not running), `not_trusted` (Accessibility missing), `unsupported_version`, `labels_missing`, `no_project`, `ambiguous_project`, `screen_locked`, `not_on_screen`, `user_active` (keyboard or mouse busy for 2 minutes) and `locked` (another desktop run holds the app). In every one of them nothing was pasted or sent.
- The model and reasoning level are the app's own: the desktop runner refuses `--model`. The permissions preset (`Request Review`, `Default`, `Auto`, `Turbo`) is the user's and never changed; under `Auto` and `Turbo` the app may run commands and edit files without asking.
- Not supported on desktop: image work, choosing a model, resuming a conversation, `--swarm`, the review gate and usage.
- Earlier Antigravity reviews measured low acceptance (8% and 46%); the agybird coordinator confirmed on 28/11/2026 that the in-app agent can run shell commands under Turbo (not verified live), and that raw `gh` would bypass the review markers.
- Planned: finolabs/agybird#59 (`docs/specs/desktop-sessions.md`, open, docs only) moves to a project per worktree and up to 5 desktop runs at once.

## Owner decisions (Fio, 28/11/2026)

1. Roles: Antigravity comes back as a worker, a code reviewer and a security reviewer.
2. Transport: agybird desktop first (`--via desktop`, or agybird `setup --transport desktop`). `agy -p` is a fallback only when desktop cannot be used: not macOS, the app not running or not signed in, Accessibility missing, or blocked for too long (for example a locked screen during an afk lease). A task's own failure never switches transport. The quota probe `agy -p /usage` stays as it is.
3. Desktop may run at any time. `blocked: user_active` and the other `blocked` states mean "not run yet": retry later, and do not count them as model failures, quality data or quota.
4. Parallel slots for Antigravity follow the installed agybird version: 1 for v0.4.8 (one `~/.agybird/desktop.lock` per machine), up to 5 once finolabs/agybird#59 ships.
5. The model is whatever the app has set; the ledger and the brief record it as set by the app, and `--model` is not relied on.
6. A reviewer posts its own markers by running `python3 scripts/post_review.py` from the checkout under the Turbo or Auto preset, never raw `gh`; pilot it on one real pull request before relying on it. Coordinator relay is the fallback (the standing relay in [CLAUDE.md](../../CLAUDE.md) "Reviews").
7. Briefs carry the limits the heavy-job gate cannot enforce inside the app: no push, heavy tests only through `heavy_run.py`, edits only inside the given worktree.
8. Re-adding Antigravity to `## Assignment matrix` in the user's host config happens through `/setup add roles` (or `delegation`) with a preview and the owner's yes; the pull request changes no machine file.

## Design (implementation choices in this pull request)

- **Not run yet is `deferred`.** `ledger.py finish --outcome deferred` closes a dispatch that a desktop `blocked` envelope never started. `ledger.py summary` leaves `deferred` records out of every row (its `n`, rates, medians and the quota and error counts), as it does records closed late. `project_progress.py` and `nav_state.py` know the word. A retry is a new dispatch. The CLI runner's own `blocked` (a run whose tools were blocked) keeps the `blocked` outcome: it ran. Enforcer: `ledger.py`.
- **One machine-wide Antigravity slot.** `parallel_slots.py check --family antigravity` also counts open Antigravity dispatches of every project against `ANTIGRAVITY_MACHINE_SLOTS` (1, for agybird 0.4.8). `status` reports it as `families.antigravity.machine`. A release raises the constant after finolabs/agybird#59 ships, in a pull request that says which agybird version it follows. The `agy -p` fallback shares the slot, which is conservative. Enforcer: `parallel_slots.py` reports; honoring it stays advisory. A second run that starts anyway gets `blocked: locked`, which is `deferred`.
- **Review form `desktop`.** `review_route.py` prints `desktop` as Antigravity's form, so a coordinator starts it through agybird's desktop transport, not `agy -p`.
- **Model label `app`.** A desktop dispatch is recorded with `--model app` (decision 5); the matrix line for Antigravity names `app` as its model. `ledger.py` warns, never refuses, when the matrix lists another name.
- **Docs.** The `delegate` Antigravity page (transport order, the desktop envelope with every `blocked` reason, the fallback rule, the model, the brief limits, the project the app needs), `agents.md`, `host-template.md`, `budget-and-liveness.md`, `parallel-dispatch.md`, `review-gate` `reviewers.md` and `relay-and-posting-setup.md` (posting from the app with `post_review.py`), the setup roles and delegation references, help pages, README, [PRIVACY.md](../../PRIVACY.md) ("Where your data goes": the desktop app), CHANGELOG and `docs/how-it-compares.md`.

## What does not change

- The quota probe keeps `agy -p /usage --output-format json`; a desktop-only user without `agy` reads Antigravity quota as unverified.
- No hook, no new network call and no new command run by the plugin: the coordinator starts agybird, which drives the app.
- The heavy-job gate does not reach inside the app (decision 7 puts its limits in the brief).
- The pull request edits no file on the user's machine (decision 8).

## Open

- Decision 6's pilot: one real pull request reviewed by Antigravity that posts both markers with `post_review.py` from the app. Until it passes, the coordinator relays (`--relay-reviewer antigravity`).
- The slot constant after finolabs/agybird#59 ships.
- Whether the app's project for a worktree must be opened by hand for each worktree on 0.4.8 (`no_project`); #59 creates projects on demand.
