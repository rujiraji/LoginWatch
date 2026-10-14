# Implementation plan

Project owner: requirements, design decisions, phase review, and acceptance.
Codex: implementation, tests, documentation, and verification evidence.

## Status

| Phase | Status |
| --- | --- |
| 1. Parser and activity summary | Accepted |
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

Phase 1 is accepted following the owner's independent review. Finalize its
documentation on `phase-1-core` and open a PR into `main`; the owner performs
the merge. Phase 2 has been assigned conditionally on that merge. Do not begin
Phase 2 while Phase 1 remains unmerged.

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
failures are exercised by subprocess tests. The original implementation
workspace lacked Git metadata, so status/diff checks were unavailable at that
time; this is a historical limitation, not the current repository state. All
events are kept in memory. Detection, configuration, export, and release
delivery remain planned.

## Phase 1 acceptance and independent review

The owner accepted Phase 1 based on independent review of commit
`aaa183c0adfe37a734a5431bf8b1db51b930ce22`. The following results were reported
by the owner; they are not checks run by Codex:

- Environment: Linux, Python 3.12.14.
- All 27 tests passed.
- Sample output matched documented expectations.
- Additional checks passed for a 120-event dataset, timezone boundaries, and invalid UTF-8 after valid data.
- No blocking issues were found. Python 3.11 remains unverified.

## Phase 1 acceptance-handoff checks by Codex

On 2026-10-14, Codex verified the current workspace is the actual checkout for
`https://github.com/rujiraji/LoginWatch`. `origin` uses that repository URL.
The working tree was clean, `HEAD` and `phase-1-core` pointed to the reviewed
commit, and `git diff aaa183c0adfe37a734a5431bf8b1db51b930ce22 --` was empty
before documentation edits. No repository was initialized or implementation
overwritten.

Checks run by Codex on Windows, Python 3.14.6:

| Command | Result |
| --- | --- |
| `python --version` | `Python 3.14.6`, exit 0 |
| `python -m unittest discover -s tests` | 27 tests passed, exit 0 |
| `python loginwatch.py samples/sample.log` | Exit 0; 9 events, 4 successes, 5 failures, 3 IPs, 5 usernames, 2 blank lines, 4 skipped lines |
| `git fetch origin` | Completed successfully; `origin/main` remained at planning commit `2f3759d168b4972dd072618a5945d2d8f1af1415` |

The existing local `phase-2-detection` branch was inspected: it pointed to the
reviewed Phase 1 commit and had no additional commits or working-tree changes.
It was left unchanged. No Phase 2 implementation has begun.

Next step: the owner merges the Phase 1 PR. Then update `main` with a
fast-forward-only pull and inspect the existing `phase-2-detection` branch
before reusing it for the assigned detection work. Do not merge PRs as Codex
or begin Phase 3.
