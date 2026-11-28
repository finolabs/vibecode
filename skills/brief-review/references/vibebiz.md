# Reading a vibebiz idea folder

vibebiz packages a business idea for a board and a tech team. Its idea folder keeps every answer the owner gave, so read the files, not only the exported pages.

| File | Read it for |
| --- | --- |
| `spec.md` | The requirement in Spec Kit format: Problem & Why, Outcome, Alternatives, AI-fit, Cost & Risk, Clarifications, user stories with priorities and Given/When/Then scenarios, functional requirements (FR-###), key entities, success criteria (SC-###), assumptions. The source of truth. |
| `exports/spec.md` | The snapshot handed to the tech team. When it differs from `spec.md`, report the difference: the export is stale or the folder moved on. |
| `plan.md` | The rollout and the order the owner expects. |
| `decisions.md` | What the owner already decided, with dates. Do not reopen a settled decision; when you disagree, say so as a recommendation with the reason. |
| `open-questions.md` | Questions still open, with blocking marks and owners. Check each is still open in `spec.md`, and add the ones you find. |
| `assumptions.md` | What the plan takes for granted. Each one is a risk to check. |
| `glossary.md` | The terms. A term the spec uses that is missing here is a gap. |
| `coverage.md` | Which categories are clear, deferred or missing. A deferred category with no reason is a gap. |
| `checklists/tech.md`, `checklists/board.md` | The readiness checks vibebiz ran. A ticked item is the owner's claim; check the ones your assessment touches. |
| `exports/tech-prd.html`, `exports/board-deck.html` | The views people read. Compare their figures with `spec.md` and `exports/data.json`; a figure that differs between views is a contradiction. |
| `exports/data.json` | The figures behind the views, with their sources. |

A folder without `spec.md` is not a packaged idea: read what is there as a plain brief and say the package is incomplete.

Write `tech-review.md` at the top of the idea folder, beside `spec.md`, after the user's yes.
