# Release 0.3.4: scope

Status: accepted; prepared, not yet tagged.

## What shipped

| Pull request | Change |
| --- | --- |
| 391 | `main` moves to `0.3.4-dev`; v0.3.3 recorded as released. |
| 392 | CI runs the script tests in four parallel shards (`scripts/ci_shard.py`); `validate` waits for the checks and the four shards. |
| 393 | `delegate_env.py` closes the child's stdin, so a delegated `codex exec` never waits on it. |
| 394 | `post_review.py` keeps Codex's own loopback sandbox proxy for `gh` (only with the sandbox marker, `http`, a loopback host, a port and nothing else), so a sandboxed Codex reviewer posts its own markers. |
| 395 | The rule: the fourth scoped exception in `CLAUDE.md` becomes a removal note; the Jev judge is retired (owner decision 26/11/2026). |
| 396 | `judge.py` (four copies) and `verify_claim.py` (two copies) make no network call and read no key; `PRIVACY.md` drops the TypeSafe call. |
| 397 | Skills, setup docs, the navigator, help, README, the Codex manifest description, upgrade notes and four diagram pairs name only the small host model. |
| this | Version 0.3.4, dated changelog, README release section, the drift fixes below and the `0.3.4/codex-sandbox-posting` upgrade note. |

## Drift review

Checked against the head of pull request 397 for every pull request from 391 to 397, surface by surface. `CLAUDE.md` was read, not edited.

| Surface | Result |
| --- | --- |
| README skill table, `delegate` row | Drifted with 395 to 397: named "the configured judge". Now "the host-model judge". |
| README skill table, `checks`, `status`, `afk` rows | Current: `afk` row fixed in 397 (the table comes from the host's small model); `checks` and `status` name host/judge receipts, which remain. |
| README setup feature table, `roles` row | Drifted with 397: offered "the judge". Now says setup no longer asks for one and an existing `Judge:` line reads as the host. |
| README setup modes table, Advanced row | Drifted with 397: "optional roles/judge". Now "optional roles". |
| README privacy and judge paragraphs | Current (397). |
| README host facts sentence | Drifted: listed "the configured judge" among `host.md` facts. Removed. |
| README release section and documented-release line | Added the 0.3.4 section; the line names 0.3.4 and `0.3.5-dev`. |
| README diagram alt text | Current (397). The settings-scopes alt still lists "judge" among `host.md` contents, which is true: the matrix keeps its `Judge:` line. |
| README file layout | Current: `scripts/ci_shard.py` is covered by the `scripts/` line. |
| `skills/help/references/map.md` | Drifted with 395 to 397: the `delegate` row named "the configured judge". Fixed. The `ci_shard.py` row landed with 392; the `judge.py` row with 397. |
| `skills/help/references/skills/*.md`, `tips.md` | Current: none described Jev, stdin or the sandbox proxy. |
| `skills/help/references/troubleshooting.md` | Current: rows for the stdin hang (393) and `cannot-post: no-network` (394) landed with them. |
| `skills/setup/references/check.md` | Current: no hook changed in this release; the companions line changed in 397. |
| `skills/update/references/upgrades.json` | Had `0.3.4/jev-retired` (397). Added `0.3.4/codex-sandbox-posting` (394): a user's own Codex command needs the proxy flags to post. Nothing for 392 or 393, which need no user action. |
| `PRIVACY.md` | Current (396, 397): the only network call is the update check; the "Judge" section describes the host judge and the retirement. |
| `docs/how-it-compares.md` | Current: it does not describe the judge, stdin or posting. |
| `docs/diagrams/*.html` and `assets/*.png` | afk mechanism, away decision sequence, skills architecture and task lifecycle updated and re-rendered in 397. Others do not show the judge. |
| `docs/specs/index.md` | Added this record's row. |
| `CHANGELOG.md` | Unreleased matched the merged pull requests once 392 (CI shards) and 397 (setup and docs) were added under Changed; moved to 0.3.4. |
| Codex manifest `longDescription` | Current (397). Claude and Antigravity manifests do not mention the judge. |

`readme_check.py` and `check-references.py` pass on this branch.

## Owner decisions

- 26/11/2026: retire the Jev judge; the small host model is the only judge, in three pull requests (395 rules, 396 code and privacy, 397 docs and setup).
- 26/11/2026: Codex reviews keep running in the sandbox with the network proxy for `api.github.com` and post themselves (394); `danger-full-access` is not used for posting.
- 27/11/2026: finish the backlog, release and publish this version (the owner's goal during an away lease).

## The upgrade

- A `Judge: jev` line in `## Assignment matrix` reads as the host model and `judge.py` says so once; `TYPESAFE_API_KEY` is no longer read; keep the line or change it to `Judge: host`, since deleting it makes the matrix invalid (`0.3.4/jev-retired`).
- To let a Codex reviewer post from its sandbox, add the network proxy flags for `api.github.com` to its command, as `delegate`'s Codex notes show (`0.3.4/codex-sandbox-posting`).

## Known follow-ups

- afk's credential floor refuses any path containing `sk-` after a letter (such as `task-lifecycle`), because the token prefix pattern in `secret_patterns.py` has no left word boundary. The task lifecycle diagram edit waited for the owner's return for that reason. Fix it in its own pull request with tests.
- `matrix_setup.py --judge` still accepts `jev`; both values mean the host model. Dropping the flag is a later, breaking change.
- A real upgrade from 0.3.3 on a user's machine remains unverified.
