# Codex repository instructions

## Read first

Read README.md, docs/SPEC.md, and docs/PLAN.md before implementation. The project owner selects the current phase and accepts completed work. Follow the owner's current instructions if they change this baseline; update affected documents so the repository stays consistent.

## Scope and architecture

- Implement only the assigned phase. Record future ideas without implementing them.
- Keep parsing, detection, and reporting separate; the CLI coordinates them.
- Use Python 3.11+ and the standard library initially.
- Prefer clear, small functions and explicit data models over unnecessary abstractions.
- Keep rules deterministic and explainable. Findings must contain reasons and supporting evidence.
- Do not add a database, dashboard, integrations, external services, or dependency framework without a scope change.

## Data and repository hygiene

- Use synthetic logs and documentation IP addresses in samples and tests.
- Do not commit real credentials, private log files, or machine-specific configuration.
- Read input files without altering them.
- Preserve unrelated user changes. Do not publish, push, or send reports externally without an explicit instruction.

## Verification

- Add tests for meaningful behavior and failure modes in the assigned phase.
- Use standard-library unittest; run `python -m unittest discover -s tests` and the documented sample command.
- Report exact commands, results, and any environment limitations. Do not claim checks ran when they did not.
- Check actual fixture results against expected values independently stated in the documentation.
- Fix relevant failures before reporting the phase implemented.

## Documentation and handoff

- Update README and affected specification sections when behavior changes.
- Distinguish planned features from verified functionality.
- Mark a completed phase Implemented — awaiting review, not Accepted.
- Provide a brief explanation of the components, their inputs/outputs, and how they connect; a line-by-line explanation is unnecessary.
- At the phase boundary, report changes, verification, limitations, and review steps. Wait for the next phase assignment.
- Keep portfolio and résumé claims grounded in implemented behavior and the owner's actual contribution. Do not invent usage or impact metrics.
