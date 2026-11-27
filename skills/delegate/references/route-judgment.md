# Route judgment

The configured judge informs material unresolved grade and route questions; the coordinator owns the decision.
Settled user choices, project rules, reachability, quota and deterministic filters take precedence. A single
remaining candidate needs no question. Use the rules in `delegate` first, then one narrow English statement
with the minimum supporting evidence, as data, through `scripts/judge.py ask --site delegation`.

## Which judge

The judge is the host's small model on its fast tier; supply its answer to `judge.py check-host`. A matrix `Judge:` line (`host` or the retired `jev`) reads as the host. A `yes` needs a verbatim quote with at least eight
alphanumeric characters. `judge.py` makes no network call. The script
caps each field and body and rejects secrets and machine paths before the question is accepted.

## Evidence and fallback

Use only the brief's goal, acceptance, affected areas and risk flags needed to test one proposed grade or route.
Never send code, secrets, personal data or customer records. Instruction-file checking is separate: only with
`Instruction check: on` in canonical config, using the screened payload from `checkup.py`, never as part of a routing question.
The instruction check uses the small host model.

Only a validated response may be recorded as `--route-by judge`. Every `no` or `insufficient` goes to the coordinator.
Without a usable small-model answer, follow the conservative table choice and record `--route-by table`.
Never store questions or answers in the ledger, and reuse a judgment only while its task, brief and candidate state match.

## Receipt after each decision

Advisory (agent judgment): after each judge decision, run
`python3 -I <delegate folder>/scripts/record.py judge --site route --grader judge --result <validated|unverified> --followed <yes|no|na>`.
Use `validated` only for a usable response, otherwise `unverified` with `followed na`. For a host fallback record
`record.py judge --site route --grader agent --result validated --followed na` only after checking its answer. The command prints only fixed
fields; consented hooks store those fields, never the question or answer. No judge grants acceptance or permission.
