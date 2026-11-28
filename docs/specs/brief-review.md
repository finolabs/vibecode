# Brief review: the tech side reads a business brief

Status: accepted; owner decisions 28/11/2026. Target release 0.3.5 (owner, 28/11/2026).

## Why

Owner direction, 28/11/2026: a business brief, a PRD or a requirement file reaches the tech side, often as a package from vibebiz (a board deck, a tech PRD and a Spec Kit requirement file built from an idea folder). Nothing in the pack covers the step between receiving it and building:

- `shape` interviews the user about an idea; it does not read and assess a document someone else wrote;
- `advisor` gives a second opinion on a question, not a structured reading of a brief;
- the `navigator` agent checks a running spec against its anchors, after work has started;
- `coding-router` on the Spec Kit path writes the spec, which already assumes the brief was understood and accepted.

vibebiz's `continue` records that the tech team reviewed the estimates, but nothing on our side produces that review.

## Settled decisions

| # | Decision | Owner's answer (28/11/2026) |
| --- | --- | --- |
| 1 | Input | Any brief, PRD, requirement or spec; a vibebiz idea folder is recognised and read with its decisions, open questions, assumptions, glossary and checklists. |
| 2 | Output | A `tech-review.md` beside the brief, written after the user's yes, plus a short summary in chat. |
| 3 | Depth | Explain in technical terms; find ambiguity, contradictions and missing measurable criteria; assess risk and feasibility; check estimates as S, M or L ranges labelled as estimates; recommend scope cuts and an order. |
| 4 | After the review | Propose only: send the questions back to the business side (for a vibebiz idea, through `vibebiz:continue`) or start building through `coding-router` (Spec Kit when the repository uses it). The user decides; the skill starts neither. |
| 5 | Name | `brief-review`. Its description keeps it apart from `review-gate`, which reviews code. |
| 6 | Invocation | Model-invoked: the agent loads it when the user asks to read, explain, assess or review a brief, PRD, requirement or spec, or hands over a vibebiz package. |
| 7 | Second opinion | Runs `advisor` without asking when a trigger hits: the brief uses AI, handles personal customer data, moves money or takes payments, or the estimate is L or larger. Running `brief-review` on such a brief counts as the user's request for that one opinion. |
| 8 | What the advisor gets | The whole idea folder (or the brief and the files beside it). [PRIVACY.md](../../PRIVACY.md) "Where your data goes" says so. |
| 9 | Language | The review follows the brief's language; IDs (FR-###, SC-###, user story numbers) and technical names stay as written. |
| 10 | Release | 0.3.5. Tests and examples use synthetic briefs; nothing from vibebiz's own examples is copied (vibebiz is under the PolyForm Noncommercial License). |

## Enforcers

Every rule in the skill is advisory (agent judgment). No hook or script enforces the procedure; the trigger check before release is the only test of when it fires.

## Surfaces

The skill, its help page, `map.md`, `contents.md`, the README skill table and count, the manifest and catalog descriptions (26 skills), the skill lists in `fnl_metrics.py` (every copy), [PRIVACY.md](../../PRIVACY.md) and [CHANGELOG.md](../../CHANGELOG.md).
