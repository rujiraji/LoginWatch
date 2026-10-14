# Implementation plan

Project owner: requirements, design decisions, phase review, and acceptance.
Codex: implementation, tests, documentation, and verification evidence.

## Status

| Phase | Status |
| --- | --- |
| 1. Parser and activity summary | Implemented — awaiting review |
| 2. Detection and evidence | Planned |
| 3. Configuration and JSON reports | Planned |
| 4. Release and portfolio delivery | Planned |

Use Planned, Ready to implement, In progress, Implemented — awaiting review, or Accepted. Codex records implementation and checks; owner review determines acceptance.

## Phase 1 — Working core

Build models.py, parser.py, reporter.py, and loginwatch.py. Add samples and standard-library unittest tests. Implement only the Phase 1 input and summary contracts in SPEC.md. No analyzer, dashboard, configuration, or export yet.

Acceptance:
- CLI parses the documented success/failure forms including invalid usernames and IPv6.
- Summary matches independently documented fixture counts.
- Malformed and unsupported lines are counted; blank lines do not count as skipped.
- Empty input is handled and unreadable/invalid UTF-8 input returns an actionable error.
- README contains setup, run instructions, and exact verified sample output.
- Tests and sample command pass; component explanation is provided.

## Phase 2 — Detection

Add analyzer.py, findings, the three default rules, and console findings with supporting evidence. Implement time ordering, boundary behavior, and episode suppression from SPEC.md.

Acceptance:
- Each rule triggers on its known fixture and remains quiet below threshold.
- Success correlation requires the same IP and account.
- Exact window boundaries, out-of-order events, mixed offsets, and interleaved events behave as specified.
- Each finding explains the trigger and identifies its source evidence.
- Repeated findings follow the documented episode policy.
- Relevant tests pass and sample findings match documented expectations.

## Phase 3 — Usable release

Add validated optional JSON configuration, JSON report export, and
configuration/output error handling. Extend the CLI help and input handling
already delivered in Phase 1. Keep console output usable.

Acceptance:
- Defaults preserve Phase 2 behavior; a custom threshold fixture demonstrates a controlled behavior change.
- Invalid configuration is rejected clearly.
- Exported JSON matches the documented schema and supporting events.
- Equivalent runs yield stable analysis data and ordering.
- Output failures return nonzero status with clear messages.
- README documents configuration, exports, and log-data sensitivity.

## Phase 4 — Delivery

Prepare normal and suspicious demo cases, a walkthrough, final documentation, and a proposed résumé bullet based on actual delivered behavior. Prepare a reviewable release; publishing or pushing to external repositories requires the owner's explicit instruction.

Acceptance:
- A fresh checkout can run using README instructions and Python 3.11+ without third-party dependencies.
- Full test suite and documented demo commands pass.
- Owner can explain parser → events → detection → findings → report and the key limitations.
- Demo explains why each finding triggers and shows a quiet normal case.
- Release notes state verified functionality, test environment, and limitations.
- Résumé wording accurately represents owner work and AI assistance, with no invented impact numbers.

## Phase handoff

After each phase, Codex reports changed components, commands executed, results, known limitations, and a brief architecture explanation. Update this file with implementation status and evidence, then stop at the phase boundary for review.

## Current assignment

Phase 1 implementation is complete and awaiting owner review. Stop at this
phase boundary; Phase 2 requires the owner's next assignment.

## Phase 1 implementation and verification

Implemented on 2026-10-14 by Codex under the owner's Phase 1 assignment:

- `models.py` defines immutable events, parser results, and activity summaries.
- `parser.py` reads UTF-8 files without changing them, validates the documented SSH format, normalizes UTC/IP values, preserves event evidence/source order, and counts blank/skipped lines separately.
- `reporter.py` converts parsed events and line counts to the seven-field summary and console text.
- `loginwatch.py` coordinates parsing/reporting, argparse help, and concise file/encoding errors.
- `samples/sample.log` and `samples/README.md` supply synthetic observations and independently specified expected outcomes; tests verify those outcomes, meaningful validation failures, and CLI behavior.

Verification environment: Windows PowerShell, Python 3.14.6, standard library
only. Exact commands and final results:

| Command | Result |
| --- | --- |
| `python --version` | `Python 3.14.6`, exit 0 |
| `python -m unittest discover -s tests` | 27 tests passed, exit 0 |
| `python loginwatch.py samples/sample.log` | Exit 0; 9 events, 4 successes, 5 failures, 3 IPs, 5 usernames, 2 blank lines, 4 skipped lines |

The full verified sample output is in README.md. These counts agree with the
line-by-line fixture expectations in samples/README.md. Initial testing caught
Python 3.14 accepting hour 24; explicit hour/minute/second validation fixed the
failure and keeps the documented format consistent across Python versions.

Limitations: Python 3.11 was not tested; compatibility is
targeted, not demonstrated on every version. Permission denial is simulated
with a mock, while actual missing-file, directory-input, and invalid-UTF-8
failures are exercised by subprocess tests. No Git metadata exists in this
workspace, so status/diff checks were unavailable. All events are kept in
memory. Detection, configuration, export, and release delivery remain planned.

Owner review: rerun the two README commands, compare the sample output with
the documented fixture expectations, and review the input grammar and component
flow. The owner decides whether to accept Phase 1 and assign Phase 2.
