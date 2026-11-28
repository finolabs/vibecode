# brief-review

Typed by the user, or loaded by the agent when the task matches.

**What it does.** Reads a business brief, PRD, requirement or spec someone handed over, or a vibebiz idea folder, from the tech side. It restates what the brief asks for in technical terms, lists gaps (ambiguity, contradictions, untestable requirements, success criteria with no baseline or way to measure), assesses risk and feasibility, sizes each user story and the whole as S, M or L, always labelled as an estimate, and recommends what to cut and the order to build in. It shows a summary in chat and offers to save the full review as `tech-review.md` beside the brief, in the brief's language. It builds nothing and starts nothing.

**When to use it.** Someone hands you a brief and you need to understand it, judge whether it is ready to build, or answer the business side with questions and an estimate.

**Type:** Claude Code `/finolabs-vibecode:brief-review` or `/brief-review`; Codex `$brief-review`; Antigravity `/brief-review`. Argument: `<path to the brief, PRD, spec or idea folder>`.

## Tips

- For a vibebiz package, point it at the idea folder, not only the exported pages: it reads the decisions, open questions, assumptions, glossary and checklists too.
- When the brief uses AI, personal customer data or money, or it sizes the work L or larger, it runs `advisor` without asking and gives that agent the whole folder; that agent's provider processes it. Say "no advisor" if you do not want that.
- After the review it offers two paths: send the blocking questions back (for vibebiz, the owner answers them with `vibebiz:continue`), or build through `coding-router`.
- It is not a code review; that is `review-gate`. To shape your own idea, use `shape`.
