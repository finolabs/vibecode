# Release 0.3.3: scope

Status: implemented; release prepared, not yet tagged.

## What shipped

| Pull request | Change |
| --- | --- |
| 345 | `main` moves to `0.3.3-dev`; v0.3.2 recorded as released. |
| 346 | A catalog pin (existing entries' `source.ref` moved to a release tag, and their descriptions) takes the low-risk lane; `merge_check.py --lane` decides. |
| 347 | Each release moves `ref` to the new tag in every host catalog that pins the plugin, Codex included (`versioning`, `update` hosts, `plugin-packaging` catalogs). |
| 348 | The live check of the Codex catalog pin: a refresh installed 0.3.2 from a `url` source pinned to `ref` v0.3.2 (codex-cli 0.169.0). |
| 349 | Compaction setup by session kind: the saved threshold serves task sessions, setup shows the `CLAUDE_CODE_AUTO_COMPACT_WINDOW=<tokens> claude` launch line for a coordinator, and `--clear-model-overrides` removes per-model values. |
| 350 | `select_tests.py` selects a module that declares `# select-tests: reads <folder>/`; the worktree sweep reads the user's global ignore file, so merged, clean worktrees are candidates again. |
| 351 | The per-model clause of the compaction nudge rule (eighth scoped exception in `CLAUDE.md`), with `PRIVACY.md` and the spec. |
| 352 | A split for an operator that ends a word in the afk check hook; removed with the hook in 360. |
| 353 | The compaction nudge follows the session model's `modelSettings.<model>.autoCompactWindow`; `compact_setup.py --model <id>` saves a threshold for one model. |
| 354 | The afk hook tokenizer spec (design only); deferred when the hook was removed, and its implementation, PR 358, closed unmerged. |
| 355 | `delegate` removes finished runs' merged, clean, pushed worktrees (`ledger.py start`, `finish`, `clean-worktrees`, and the merge notice); `FNL_WORKTREE_CLEAN=manual` or `off`. |
| 356 | Session titles: the agent names the session in its first turn whatever the task, and sessions it starts get the same format (`tidy`, the session-start rules). |
| 357 | The afk check hook read a wrapper name as a wrapper only where a command starts; removed with the hook in 360. |
| 359 | `coding-router`'s Spec Kit adapter covers `specify workflow` runs: the depth gate still decides, gate verdicts are the user's, and each agent step is a ledger dispatch. |
| 360 | The afk check hook is removed (owner decision, 18/11/2026); the tenth scoped exception becomes a removal record and the agent runs `afk.py check` itself on every host. |
| 361 | The afk decider spec: a stop hook, a permission hook, merge by the decider and native deny rules for the credential floor; owner decisions 1 to 6. |
| 362 | `/setup instructions` scans existing instruction files for lines that stop `afk` or `delegate` and proposes replacements; the contract template names the lease exception. |
| 363 | The afk decider on Claude Code: the afk stop hook (`Stop`), the afk permission hook (`PermissionRequest`, approvals by request digest), `merge: decide` per repository, `afk_native_rules.py`; the eleventh and twelfth scoped exceptions in `CLAUDE.md` and two `PRIVACY.md` sections. |
| 364 | The UI review gate spec (`docs/specs/ui-review-gate.md`); no code. |
| 365 | `/setup add quota --weekly-floor <family>/<label>=<percent>`: routing treats that install's weekly pools below the floor as out of quota. |
| 366 | The UI review gate (`ui-review-gate`) skill, implementing docs/specs/ui-review-gate.md: four modes on WCAG 2.2 AA, read-only measurement snippets, report-only and advisory; seven Codex review rounds on the target-size inline exception. |
| 367 | The inline target check skips hidden elements (last LOW finding of 366). |
| 368 | The first release pass: the drift review below, the Codex hook trust note, the README release section, changelog and manifests. |
| 369 | The afk goals spec (`docs/specs/afk-goals.md`); no code. |
| 371 | Cross-skill gaps of 0.3.3: `merge_check.py --independent` counts a family under its weekly floor (above 10%) as present; headless Claude children run with `FNL_AFK_STOP=off` and `FNL_AFK_PERMIT=off` (owner decision, 19/11/2026); `merge: decide` counts as Merge yes for the standing security relay (`CLAUDE.md`); `ui-review-gate` in every workflow adapter's review step; the request-to-merge diagram. |
| 372 | `tidy` turns a session's remote access off before archiving it (Claude Code desktop: Remote Control, then archive); `delegate`'s coordinator sessions point to it. |
| 373 | afk has one mode (owner decisions 1 to 4, 19/11/2026; `docs/specs/afk-one-mode.md`): `strict`, its lists, categories, Merge answer and the per-repository limits are removed; `Lease hours` stays; old `Mode: strict` and limit lines start normally with one notice line each; the stop hook's limit escape is the lease end only; the fallback under a lease needs only the lease, the author's family and the fallback line. Pull request 370 (decision 5, the strict syntax allowlist) closed unmerged. |
| 374 | afk report quick wins: a decision id typed in another case is accepted and recorded as generated; headless Claude children also run with `FNL_PROOF_NUDGE=off`; `delegate` dispatch says a test step's variable reaches a heavy job only through `heavy_run.py run --pass-env NAME`. |
| 375 | afk goals (owner decisions 19/11/2026; `docs/specs/afk-goals.md`): `afk.py goal` keeps a private queue per repository, `log --item` closes items, `idle` is refused while one is open, the stop hook ends a turn only on a current `idle` record for the hook folder's repository, plain `stop` is refused for `stop --all`, `effective` prints `Project settings`, the permission hook allows `goal`, the away line asks a joining session to run `goal`; `/afk start [hours]` wakes coordinators and runs the merge-blocker preflight; the eleventh and twelfth scoped exceptions and three `PRIVACY.md` sections. |
| 376 | Light stored checks (`checks`, `setup`; [spec](checks.md#light-checks-2026-11-19)): a check in the approved `checks.json` may carry `"heavy": false` and then runs directly, outside the heavy-job lock and load gate, still refusing during a pause (77), waiting only on critical memory pressure (75) and stopping its process group after `Max job minutes` (124); `/setup add checks` saves test-module checks light by default, `--light` and `--heavy` override, and the mark is inside the approved digest. |
| 377 | UI review marker, opt-in per repository (`ui-review-gate` decision 4, owner decision 19/11/2026): a base whose `## Agent skills` section names `ui-review-gate` makes the router marker carry `ui=yes` or `ui=no`, and `merge_check.py` requires a `kind=ui` review approving the head for `ui=yes`; `/setup` offers the UI line. |
| 378 | `status`, `review-gate` and `coding-router` disclose branch-only detail into their `references/` folders, so each `SKILL.md` stays under 10,000 bytes; no rule changes. |
| 379 | Backlog LOW and docs items (`claude/backlog-lows`): the dashboard shows a weekly pool under its install's recorded weekly floor amber, as routing counts it out (`refresh.py` `floor` and `below_floor`, `PRIVACY.md`, the dashboard spec); `merge-gate.md` and the autopilot spec name the repository scoping of merge pins and what an unwritable afk log does, with a test; `shape` in the skills architecture and the main checkout in the delegation sequence (PNGs and README alt text); the `setup` beginner line names the commands that bring skipped steps back. |
| 380 | The compaction nudge asks the agent to hand the user a ready `/compact` line that names the saved handover; `tidy` ends the line with `handover_state.py read --session <id>` (on Codex a second line after a bare `/compact`, on Antigravity the `/new` or `/fork` text). The hook reads the same fields as before. |
| 381 | Reset-based quota freshness and bounded unexpected-shape retries; API-billed Claude no-limits status; expired pool display (owner decisions, 19/11/2026). |
| 382 | The second record pass: rows 368 to 381, the second drift pass below and the edits it lists (README, help map, troubleshooting, the `0.3.3/light-checks` and `0.3.3/quota-reset-freshness` upgrade notes, the CHANGELOG move), and the live-browser run of the `ui-review-gate` snippets. |
| 383 | Spec status lines for the backlog (owner decisions, 23/11/2026): ledger closure, the README standard and the afk decider recorded as implemented, decision 5 closed; the merge guard `deferred; retired`; autopilot `implemented; first slice only`, remainder retired. No code. |
| 384 | The opt-in heavy-job gate on Claude Code ([spec](heavy-jobs.md) part D, the fifth scoped exception): `scripts/heavy_gate_hook.py`, a `PreToolUse` Bash group in the user's own settings, refuses a heavy command not run through `heavy_run.py`; `heavy_gate_setup.py` previews, applies and removes it; `setup add delegation` asks for it with its own question. The default load limit is 25, not 12. |
| 385 | Relay receipts ([spec](agent-roles.md) part D): `post_review.py --relay-reviewer`, `--relayed-by` and `--relay-authority` refuse a relay that does not fit and leave one receipt after the observed post; the metrics hook records a `relay` event (four enum fields), and the `status` dashboard counts relays per reviewer family and kind. |
| 386 | The README host comparison: a six-row table and a light and dark diagram (`docs/diagrams/host-vs-vibecode-*.html`); `docs/how-it-compares.md` gains proof and review rows, its host facts checked again on 2026-11-23. |
| 387 | The third record pass: rows 382 to 386, the third drift pass below and the edits it lists (README release section, help map, the `0.3.3/codex-hook-trust` note, the CHANGELOG docs entry). Tags nothing. |
| this | Plain afk lease commands (live smoke test, 24/11/2026): `/afk start` prints the exact form the afk permission hook allows and a copyable `End a turn:` idle command with this install's absolute `afk.py` path; the away line, the stop hook's fixed reason and the permission hook's fixed messages say to run lease commands alone with no shell variable, `;` or quotes; the `afk` references drop quoted labels; an invalid or pre-0.3.3 lease makes `start` and `effective` say to run `/afk stop` first. |

The changelog's 0.3.3 section holds the user-facing wording; `update` carries the 0.3.3 upgrade notes. Pull request 358 (the tokenizer implementation) closed unmerged and is not part of 0.3.3.

## Drift review

Checked against `main` at `b03334c` (after pull request 365), surface by surface, for every merged pull request from 345 to 365. `CLAUDE.md` was read, not edited. Pull request 366 merged after the first pass; its own pull request updated the README skill table and companions, the skill count in the three manifests, its help page, the help map and tips, the upgrade notes and the changelog. Checked again at `a863cce` for 366: the release section below names it; `how-it-compares.md` names no individual gate, so it was left unchanged; the `skills-architecture` diagram drifted (its gates box named only `security-review-gate`, its description said 0.3.2): the box now reads `security-review-gate · ui-review-gate` and the PNGs were re-rendered.

| Surface | Result |
| --- | --- |
| README skill table, `afk` row | Current: no Bash hook, the stop and permission hooks (363). |
| README skill table, `coding-router` row | Drifted with 359: no `specify workflow` runs. Added that the depth gate governs them. |
| README skill table, `delegate` row | Drifted with 355: did not say finished runs' worktrees are removed. Added, with `FNL_WORKTREE_CLEAN`. |
| README skill table, `setup` row | Drifted with 362: `instructions` did not list conflicting lines first. Added. |
| README skill table, `tidy`, `commit-messages`, `review-gate`, `versioning` rows | Current: the title rule (356), the sweep (350), the catalog lane (346) and the catalog pin (347) are below the level of these rows. |
| README setup feature table, `afk` row | Current: native deny rules and the repository `merge: decide` question (363). |
| README setup feature table, `quota` row | Drifted with 365: no weekly floor. Added. |
| README setup feature table, `compaction` row | Drifted with 349 and 353: no per-model threshold or coordinator launch line. Added. |
| README compaction nudge paragraph | Drifted with 353: said the nudge reads only token counts and settings. Now names the model id, in memory only, on Claude Code. |
| README install section and host table | Current: the catalog pin (347) and the merge notice cleanup (355). |
| README file layout | Current: `hooks.json` lists the afk stop and permission hooks. |
| README release section and documented-release line | Added the 0.3.3 section; the line now names 0.3.3 and `0.3.4-dev`. |
| README diagram alt text | Current: afk mechanism (360, 363), session health (356). The away decision sequence alt shows a question's path, which the decider hooks do not change. |
| `skills/help/references/skills/afk.md` | Current (360, 363). |
| `skills/help/references/skills/setup.md` | Drifted with 365: no weekly floor. Added a tip. Compaction (349, 353) and instructions (362) current. |
| `skills/help/references/skills/tidy.md` | Current (349, 353, 356). |
| `skills/help/references/skills/delegate.md` | Current (355). |
| `skills/help/references/skills/coding-router.md` | Current (359). |
| `skills/help/references/skills/review-gate.md`, `update.md` | Current (346, 347). |
| `skills/help/references/skills/versioning.md`, `plugin-packaging.md`, `checks.md`, `commit-messages.md` | Current: their tips do not describe catalog pins, the `select-tests` marker or the sweep's ignore file. |
| `skills/help/references/map.md` | Drifted: the `compact_setup.py` row had no `--model` or `--clear-model-overrides` (349, 353); the `quota_probe.py`, `review_route.py` and `quota_setup.py` rows had no weekly floor (365). Updated. The afk hook, `afk_native_rules.py`, `ledger.py`, `merge_notice_hook.py` and `select_tests.py` rows were current. |
| `skills/help/references/tips.md` | Current (355). |
| `skills/help/references/troubleshooting.md` | Current: the check hook row replaced by the stop, permission and native-rule rows (360, 363). |
| `skills/setup/references/check.md` | Drifted with 355: the list of hooks that run automatically left out the merge notice, which now starts the worktree cleanup. Added. The decider hooks (363) and the weekly floor (365) were current. |
| `skills/update/references/upgrades.json` | Had 0.3.3 notes for 349, 353, 355, 360, 362, 363 and 365. Missing: Codex hook trust, though `scripts/compact_nudge.py`, which the Codex manifest runs, changed (353) while `.codex-plugin/hooks.json` did not. Added `0.3.3/codex-hook-trust`. |
| `PRIVACY.md` | Current: "Compaction nudge" (351), "afk check hook" as a removal record (360), "afk stop hook" and "afk permission hook" (363), `afk_native_rules.py` and the worktree cleanup. Drifted with 365: "Quota probe" did not list the weekly floor line in `## Quota probe`. Added. |
| `docs/how-it-compares.md` | Drifted with 363: the merge row did not name `merge: decide`, and the `afk` row did not say blocking is the host's or name the stop and permission hooks and native deny rules. Updated. |
| `docs/diagrams/afk-mechanism-*.html` | Current: updated in 360 and 363; the PNGs were re-rendered. |
| `docs/diagrams/delegation-sequence-*.html` | Drifted with 355: step 17, the subtitle and the description said the coordinator removes the worktree. They now say `ledger.py` removes the merged, clean worktree in the background. PNGs re-rendered through the shared Chromium. |
| `docs/diagrams/session-health-*.html` | Current: updated in 356; the PNGs were re-rendered. |
| Other diagrams (away decision sequence, request to merge, settings scopes, skills architecture, task lifecycle) | Checked for the check hook, worktree cleanup, merge authority and titles; none drifted. |
| `docs/specs/index.md` | The afk decider row said decision 5 was open; now parked on 19/11/2026 and left out of 0.3.3, as the spec's Status line now says. Added this record's row. |
| `CHANGELOG.md` | Unreleased matched the merged pull requests; moved to 0.3.3 with one entry for this pull request's docs changes. |

### Second pass (after pull request 381)

Checked against `main` at `8de36e1`, surface by surface, for every pull request merged after 366: 367 to 380 (370 closed unmerged); checked again at `bc56b59` for 381, which updated `CLAUDE.md`, `PRIVACY.md`, the README host configuration paragraph, `/setup check` and the specs that stated the 8-hour or 24-hour rule. Pull requests 371, 373, 375, 377, 378 and 379 updated most of their own surfaces; this pass reads each surface again for all of them.

| Surface | Result |
| --- | --- |
| README skill table, `checks` row | Drifted with 376: did not say light checks run outside the heavy-job lock. Added. |
| README skill table, `tidy` row | Drifted with 372 and 380: no ready `/compact` line, no remote access off before archiving. Added. |
| README skill table, `afk`, `review-gate`, `ui-review-gate`, `delegate`, `status`, `coding-router` rows | Current (373, 374, 375, 377, 378): one mode, goals, the UI marker and the reference splits are below the level of these rows or already named. |
| README setup feature table, `checks` row | Drifted with 376: no light or heavy mark. Added. Other rows current. |
| README compaction nudge paragraph and host table | Current with 380: they name what the hook reads, which did not change. |
| README release section | Drifted: no light checks (376), UI review marker (377), ready `/compact` line (380, with 372) or reset-based quota freshness (381). Added four bullets. |
| README diagram alt text and file layout | Current: 373, 375 and 379 re-rendered their diagrams with the alt text; no hook was added after 375. |
| `skills/help/references/skills/checks.md`, `tidy.md`, `afk.md`, `ui-review-gate.md`, `status.md`, `brb.md` | Current: updated by 376, 372 and 380, 373 and 375, 377, 379 and 375. |
| `skills/help/references/map.md` | Drifted: the `checks` row (376), the `tidy` row (380) and the `quota_probe.py` row (381) did not name light checks, the `/compact` line or freshness by reset, `reset passed at` and `no plan limits`. Updated. The `checks.py`, afk and merge-check rows were current. |
| `skills/help/references/tips.md` | Current. |
| `skills/help/references/troubleshooting.md` | Drifted with 376 and 381: nothing for a check that waits for the heavy-job lock, or for `reset passed at` and `no plan limits` in `/setup check` and `quota_probe.py status`. Added two rows. afk rows current (373, 375). |
| `skills/setup/references/check.md` | Current: 371, 373, 375 and 377 updated it; Check does not report stored check lists. |
| `skills/update/references/upgrades.json` | Missing: 376 said its note goes in with the release entry, and none was there. Added `0.3.3/light-checks`, and `0.3.3/quota-reset-freshness` for 381, which needs no action but changes what `status` and routing show. 372, 374 and 380 need no action from the user; the Codex hook trust note already covers the changed nudge script. |
| `PRIVACY.md` | Current: 371, 373, 374, 375, 379 and 381 updated it; 376 and 380 store and send nothing new. |
| `docs/how-it-compares.md` | Current (373, 375). |
| `docs/diagrams/` | Current (the task lifecycle names only "quota read on demand", which 381 did not change): afk mechanism, away decision sequence and request to merge (371, 373, 375), delegation sequence and skills architecture (379). No diagram shows the heavy-job lock or the `/compact` line. |
| `docs/specs/ui-review-gate.md` and `index.md` | The Status line and index row said the snippets had not run in a live browser. Updated after the live run (see Known follow-ups). |
| `CHANGELOG.md` | 376's entry sat under `Unreleased` although 0.3.3 is not tagged. Moved to 0.3.3 beside 381's entry; the docs entry names this pass. |
| `skills/setup/references/check.md`, `README.md` host configuration paragraph | Current with 381: its own pull request replaced the 8-hour rule. |

### Third pass (after pull request 386)

Checked against `main` at `f5556d5c`, surface by surface, for every pull request merged after 381: 382 to 386. 382 is the second record pass itself; 383 changed only spec status lines and the index; 384, 385 and 386 updated most of their own surfaces. `CLAUDE.md` was read, not edited: 384 relied on the fifth scoped exception already recorded there.

| Surface | Result |
| --- | --- |
| README skill table, `checks`, `delegate`, `setup` rows | Current (384): the heavy-job lock is named in `checks` and `delegate`; the gate is a `setup add delegation` question, below the level of the `setup` row. |
| README skill table, `review-gate`, `status` rows, and the roles and posting paragraph | Current (385): the paragraph names relay receipts and the `/status` relay count; the rows stay at their level. |
| README setup feature table, `delegation` row | Current (384): names the heavy-job gate question. |
| README host comparison section, diagram alt text and file layout | Current (384, 386): the new section and its alt text came with 386; the layout names the host versus vibecode diagram and says the heavy-job gate lives in the user's settings, not `hooks.json`. |
| README release section | Drifted: no relay receipts (385) or host comparison (386), and the Codex line named only the compaction nudge, though `scripts/metrics_hook.py` (385) and `scripts/session_start.py`, which the Codex manifest also runs, changed since v0.3.2. Added two bullets and named the three scripts. The heavy-job gate bullet came with 384. |
| `skills/help/references/skills/setup.md`, `delegate.md`, `checks.md` | Current (384): the gate question, the load limit 25 and light checks. |
| `skills/help/references/skills/review-gate.md`, `status.md` | Current (385): the relay options and the relay count. |
| `skills/help/references/map.md` | Drifted with 385: the `post_review.py` row had no relay options and the `record.py` row no relay receipt. Updated. The heavy-job rows (`heavy_run.py` default 25, `heavy_gate_hook.py`, `heavy_gate_setup.py`) and the relay sentence in the capacity paragraph were current. |
| `skills/help/references/tips.md` | Current (384): the heavy-job gate tip. |
| `skills/help/references/troubleshooting.md` | Current (384): the gate's refusal and a gate that stopped after an update. No relay row is needed: a refused relay prints its own reason. |
| `skills/setup/references/check.md` | Current (384): Check reports the `Heavy-job gate:` line and says the settings group is not verified. 385 adds no hook. |
| `skills/update/references/upgrades.json` | `0.3.3/heavy-job-gate` (384) was present. Drifted: `0.3.3/codex-hook-trust` named only the compaction nudge script; it now names the metrics and session-start scripts too. Relay receipts need no action from the user, so no note was added. |
| `PRIVACY.md` | Current: "Heavy-job gate" (384) and the relay receipt in the metrics section (385). |
| `docs/how-it-compares.md` | Current (384, 386): 384 changed one word of the `afk` row; 386 added the proof and review rows and re-checked the host facts. The page names no individual hook, so the heavy-job gate and relay receipts sit below its level. |
| `docs/diagrams/` | Current: 386 added `host-vs-vibecode-*` with its PNGs; no other diagram shows the heavy-job gate or relays. |
| `docs/specs/index.md` | Current (383, 384, 385): the merge guard, autopilot, afk decider, ledger closure, README standard, heavy-job and agent roles rows match their Status lines. |
| `CHANGELOG.md` | Current for 384, 385 and 386 under 0.3.3; 383 changes no user-facing surface. The docs entry now names this pass. |

## Owner decisions

- 17/11/2026: a catalog pin takes the low-risk lane (346).
- 17/11/2026: compaction setup by session kind: the saved threshold serves task sessions, a coordinator gets a launch line with the variable, not `--autocompact`, and a hook that recognizes a coordinator is dropped (349).
- 17/11/2026: the UI review gate lives in vibecode as `ui-review-gate`, with WCAG 2.2 AA as its standard (spec decisions 1 to 3).
- 18/11/2026: follow Claude Code's per-model compaction threshold; the nudge may read the model id (351, 353).
- 18/11/2026: remove the afk check hook; blocking is the native harness's job (360). The seven tokenizer decisions settled the same day lapsed with it.
- 18/11/2026, afk decider ([spec](afk-decider.md)):
  1. the stop hook, a new scoped exception that may block an agent's stop once in a row under a lease (the eleventh);
  2. the permission hook, allowing only exact recorded approvals under a lease (the twelfth);
  3. merge authority: the lease's Merge answer or `open` mode, plus an optional per-repository `merge: decide` record with its own consent question;
  4. self-protection: a pull request changing the lease, setup, hooks or instruction files merges like any other when `MERGE OK` holds (the alternative taken);
  5. `check` keeps accounting, approvals and "Where it must stop" and drops its syntax allowlist and general argv classification. Parked on 19/11/2026 and left out of 0.3.3, because it redefines `strict` mode and the rules a live lease runs on;
  6. `setup` offers native deny rules for the credential floor; `afk start` warns when the host has none.
- 18/11/2026: the UI review gate is advisory in 0.3.3 (no `merge_check.py` change), runs read-only measurement snippets, adds axe-core only when the repository declares it or the user agrees, blocks below 24 px target size, reports only by default, and targets 0.3.3 (spec decisions 4 to 7).
- 19/11/2026: routing stops using an install below a weekly floor, starting with the `claudework` install at 85% of its week used (365).
- 23/11/2026: finish the whole backlog in 0.3.3, then run the drift review and the full test suite before the tag.
- 23/11/2026: the default heavy-job load limit is 25, not 12 (384).
- 23/11/2026: relay receipts count every relay (385).
- 23/11/2026: the merge guard is retired; blocking a merge is the host's own permission rules (383).
- 23/11/2026: the rest of the autopilot spec beyond its first slice is retired (383).
- 23/11/2026: afk decider decision 5 is closed, superseded by afk one mode (383).
- 23/11/2026: same-family reviews count for pull requests 383 to 386, because Codex was out of its weekly quota until 24/11/2026.

## The upgrade

- Claude Code: the afk check hook is gone and `FNL_AFK_HOOK` does nothing; under a lease the agent runs `afk.py check` itself and the host's permissions block (`0.3.3/afk-check-hook-removed`).
- Claude Code: under a lease the afk stop hook and permission hook settle stops (`0.3.3/afk-decider-hooks`); `/setup add afk` can add native deny rules for the credential floor (`0.3.3/afk-native-rules`); afk has one mode, the limits are gone and an old lease needs `/afk stop`, then `/afk start` (`0.3.3/afk-one-mode`).
- Claude Code: open a coordinator with `CLAUDE_CODE_AUTO_COMPACT_WINDOW=<tokens> claude` (`0.3.3/coordinator-threshold`); the nudge follows the session model's `/autocompact` value, and setup can save a threshold for one model (`0.3.3/per-model-threshold`).
- `delegate` removes finished runs' merged worktrees in the background; runs started before 0.3.3 stay (`0.3.3/worktree-clean`).
- `/setup instructions` flags lines that stop `afk` or `delegate` (`0.3.3/instructions-conflict-scan`).
- `/setup add quota` can record a weekly floor per install (`0.3.3/quota-weekly-floor`).
- Quota readings count until their pools reset, an API-billed Claude install shows no plan limits, and a pool past its reset shows its reset time (`0.3.3/quota-reset-freshness`).
- Saving the check list again with `/setup add checks` marks test-module checks light, so they skip the heavy-job lock; a list saved before 0.3.3 stays all heavy (`0.3.3/light-checks`).
- Claude Code: `/setup add delegation` can turn on the heavy-job gate, which refuses a heavy command not run through `heavy_run.py`; heavy jobs now wait at a load of 25 (`0.3.3/heavy-job-gate`).
- Codex: trust the plugin's hooks again with `/hooks` after the refresh; the compaction nudge, metrics and session-start scripts changed (`0.3.3/codex-hook-trust`).

## Known follow-ups

- afk decider decision 5 (drop `check`'s syntax allowlist and general argv classification) is superseded and closed (owner decision, 23/11/2026; pull request 383): `strict` is removed in this release (afk one mode, pull request 373), and pull request 370 closed unmerged.
- Live delivery of the afk stop and permission hooks on a user's machine remains unverified; the `Stop` and `PermissionRequest` schemas were checked against Claude Code 2.1.327 only.
- The new hooks load only in Claude Code sessions started after the update; a session open during the update keeps the old hook set.
- Codex: `.codex-plugin/hooks.json` did not change since v0.3.2, but `scripts/compact_nudge.py`, `scripts/metrics_hook.py` and `scripts/session_start.py` did, so Codex asks to trust the hooks again; Codex and Antigravity have no stop or permission hook, so "Decide" stays advisory there.
- The `ui-review-gate` snippets ran in a live Chromium: on 19/11/2026 through the shared Chromium over CDP, and on 21/11/2026 in Playwright's Chromium 157.0.8103.78 at 375 and 1280 px, over a live-layout fixture kept outside the repository (three 16 px buttons, one alone and two side by side, a 32 px button, a 48 px button, an inline link, faint text, a 900 px block, an unlabeled and a labeled field) and over `tests/fixtures/ui-review-gate/page.html`. All four snippets returned without an exception, and on the live fixture each known case read as expected: the three 16 px buttons blocking, the 32 px button `low`, the inline link `low` and uncertain, one contrast failure, overflow at 375 px only from the 900 px block, the unlabeled field with no label. `page.html` places boxes through style attributes that only the fake DOM reads, so its live counts differ from the unit tests by design. Every inline target exception stays marked uncertain for a check by eye; a run against a real product page remains unverified.
- Pull requests the coordinator writes itself (376 and 380 in this release) have no ledger dispatch, so `ledger.py summary` does not count them and their bodies name no ledger id; their gate is the review gate (`delegate` `references/accept.md`). The docs do not yet say how such a pull request records who wrote it.
- A real upgrade from 0.3.2 on a user's machine remains unverified.
- The plain lease command form (the last row of "What shipped") is tested offline only: that an agent under a live lease copies the printed `End a turn:` line and ends its turn waits on the coordinator's live check. `check --argv-json` and a `--note` with spaces still need quotes, so under a lease they run without a prompt only through the allow rules `/afk start` prints; without those rules each such call is denied with a request digest and goes to Decide.
- Live delivery of the heavy-job gate on a real Claude Code host remains unverified; its tests run the hook script directly.
- Every `docker compose` subcommand counts as heavy per [heavy-jobs](heavy-jobs.md) part B (`docker` with `compose`), `ps` and `logs` included; the owner may narrow the list later.
- The reviews of pull requests 383 to 386 were same-family (Claude), approved by the owner because Codex was out of its weekly quota.
- The `finolabs/plugins` catalog pins move only with the owner's go after the tag.
- Backlog LOW and docs items checked on `claude/backlog-lows` and closed without a change there:
  - K1 (`readme_check.py`, an unanchored link outside the repository): already fails as `outside the repository` on main (commit f77bd256, with a test).
  - PR 302, an end-to-end worktree remove across targets: no code left to test; afk one mode removed the worktree rule. The two-repository refusal already had a test.
  - P2 (`token_hex(2)` dispatch ids): kept; the id format is read by checks, record and afk, and `new_id` picks an unused id under the finish lock (64 tries).
  - P5 (receipts not required): settled by the owner on 15/11/2026; `--accept-unverified` needs a reason and prints a warning each time.
  - A9b (Codex `UserPromptSubmit` nudge coverage): covered by the Codex class of `tests/test_compact_nudge.py`.
  - L2 (self-attested merge head): fixed earlier; `log --kind merge --head` needs the pin of an allowed merge check of the same lease and repository.
  - Docs 17, J2 ("silent steps") and K1 (the host-judge branch of `matrix.md`'s migrate paragraph): already reworded on main.
  - Docs 18, L2 informational (`lease_guard` answers `limit` for a future start before a spent check): moot; one mode has no spent or hourly limit.
  - Docs 15: `request-to-merge` already showed `shape` and the main checkout.
