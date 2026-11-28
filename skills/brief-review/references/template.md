# tech-review.md layout

Keep the headings in the brief's language. Every finding cites where it comes from (a section, an FR or SC id, a file).

```markdown
# Tech review: <brief title>

Reviewed: <YYYY-MM-DD> · Source: <file or folder> · Verdict: <ready | ready after the blocking questions | not ready>
Second opinion: <none | advisor family and model, and where it disagreed>

## What it asks for
<problem, outcome and scope in technical terms: users, data, systems, integrations>

## Gaps
| # | Kind | Where | Finding | Blocking |
| --- | --- | --- | --- | --- |
| G1 | ambiguity, contradiction, untestable, unmeasurable or unowned | <section or id> | <what and why it matters> | yes / no |

## Risks
| # | Area | Risk | Likelihood and impact | Mitigation |
| --- | --- | --- | --- | --- |

## Estimate (an estimate, not a commitment)
| Item | Size | Rests on |
| --- | --- | --- |
| User Story 1 | S / M / L / XL | <assumptions> |
| Whole | <size> | <assumptions>; the brief's own estimate: <agrees / differs, and why> |

## Recommendation
- Cut or defer: <items>
- Build order: <smallest slice that proves the outcome first>

## Questions for the business side
1. <question> (blocking / not blocking; owner if known)

## Next step
<back to the business side with the blocking questions, or build through coding-router>
```
