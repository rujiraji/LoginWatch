# Implementation plan

Project owner: requirements, design decisions, phase review, and acceptance.
Codex: implementation, tests, documentation, and verification evidence.

## Status

| Phase | Status |
| --- | --- |
| 1. Parser and activity summary | Accepted |
| 2. Detection and evidence | Accepted |
| 3. Configuration and JSON reports | Accepted |
| 4. Release and portfolio delivery | Implemented — awaiting review |

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
- Duplicate configuration keys and unsafe integer values are rejected; effective configuration is immutable and findings show actual thresholds.
- Atomic UTF-8 export rejects input/configuration aliases, preserves existing reports on failure, and cleans up temporary files.
- Complete schema 1.0 reports have reproducible bytes and preserve every finding/evidence field, including raw source text.

## Phase 4 — Delivery

Prepare normal and suspicious demo cases, a walkthrough, final documentation, and a proposed résumé bullet based on actual delivered behavior. Prepare a reviewable release; publishing or pushing to external repositories requires the owner's explicit instruction.

Acceptance:
- A fresh checkout can run using README instructions and Python 3.11+ without third-party dependencies.
- Full test suite and documented demo commands pass.
- Owner can explain parser → events → detection → findings → report and the key limitations.
- Demo explains why each finding triggers and shows a quiet normal case.
- Release notes state verified functionality, test environment, and limitations.
- Résumé wording accurately represents owner work and AI assistance, with no invented impact numbers.
- README is a concise entry point; detailed verification history stays in PLAN, with a reproducible walkthrough and proposed release notes in separate documents.
- Minimal GitHub Actions CI runs unittest on Python 3.11 and 3.14 on Ubuntu and Windows; only observed outcomes and platform skips are reported.
- Fresh-checkout setup, demos, and JSON reproducibility checks pass without third-party runtime packages. Do not create tags or publish a GitHub release yet.

## Phase handoff

After each phase, Codex reports changed components, commands executed, results, known limitations, and a brief architecture explanation. Update this file with implementation status and evidence, then stop at the phase boundary for review.

## Current assignment

Phase 1 is Accepted and was merged by the owner via PR #1 at commit `357ea3e`.
Phase 2 is Accepted following independent review of commit
`4b51f8e998a6dfe193d2a95000859ee382c83342` in PR #2, merged by the owner at
`f179620ddd0adefde9432051b362f46633db326e`. Phase 3 is Accepted following
independent review of commit `16751333a60bec6f93ec6568a46ecefb08d63966` in PR #3.
The owner merged PR #3 at `5e7c9cac31e8ea21d581a71ab80c1abbf2c14adc`.
Phase 4 is Implemented — awaiting review on `phase-4-delivery`: concise README,
walkthrough, architecture/interview notes, proposed release/résumé wording,
minimal CI, and fresh-checkout/demo verification. Keep runtime scope unchanged.
Commit, push, open a PR using the authenticated terminal's `gh`, report actual
verification/CI outcomes and limits, and stop for independent review. Do not
merge PRs, create tags, publish a release, or claim final acceptance as Codex.

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
events are kept in memory. At the Phase 1 boundary, detection, configuration,
export, and release delivery remained planned.

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

At the Phase 1 handoff, the existing local `phase-2-detection` branch was inspected: it pointed to the
reviewed Phase 1 commit and had no additional commits or working-tree changes.
It was left unchanged. No Phase 2 implementation has begun.

The next step at that handoff was for the owner to merge the Phase 1 PR, update `main` with a
fast-forward-only pull and inspect the existing `phase-2-detection` branch
before reusing it for the assigned detection work. Do not merge PRs as Codex
or begin Phase 3. The owner has since merged Phase 1; the Phase 2 record follows.

## Phase 2 implementation and verification

On 2026-10-14, Codex found a clean checkout on `main` at merge commit `357ea3e`,
with `origin` pointing to `https://github.com/rujiraji/LoginWatch.git`.
`git pull --ff-only origin main` completed successfully (already up to date).
The existing `phase-2-detection` branch had no unique commits or changes;
it was inspected, switched to, and fast-forwarded to `main` without reset or
overwrite.

Changed components:

- `models.py`: immutable findings with deterministic source-scoped IDs, thresholds, explanations, and complete evidence snapshots.
- `analyzer.py`: sorted-view UTC analysis using the three fixed default rules, inclusive boundaries, source-line tie-breaking, and episode expiry before new failures are appended. Parsing stays independent and unchanged.
- `reporter.py` and `loginwatch.py`: preserved summary and input errors, followed by console findings with every supporting source line and raw record.
- `samples/normal.log`, `samples/suspicious.log`, and `samples/README.md`: synthetic demos and independently specified summary/finding expectations.
- `tests/`: trigger/below-threshold, boundary/just-outside, correlation/negative cases, ordering/offsets, interleaving, suppression/rearming (including silent gaps), repeated successes, deterministic IDs, exact evidence membership, normal/empty input, and CLI regressions.
- README and SPEC: current behavior, demo results, episode policy, evidence contracts, and limitations.

The parser produces immutable events and source-line counts. The CLI sends
events to the analyzer, which sorts a separate view and returns ordered
findings. The reporter formats the original summary plus finding explanations
and source evidence. Detection never changes parsed source ordering.

Verification by Codex: Windows PowerShell, Python 3.14.6, standard library only.

| Exact command | Result |
| --- | --- |
| `python -m unittest discover -s tests` | 69 tests passed, exit 0 |
| `python loginwatch.py samples/sample.log` | Exit 0; original counts unchanged, zero findings |
| `python loginwatch.py samples/normal.log` | Exit 0; 8 events, 6 successes, 2 failures, 3 IPs, 3 usernames, 0 blank/skipped lines, zero findings |
| `python loginwatch.py samples/suspicious.log` | Exit 0; 14 events, 3 successes, 11 failures, 3 IPs, 7 usernames, 0 blank/skipped lines, five findings |
| `python loginwatch.py --help` | Exit 0; summary/detection description and input-path help |
| `git diff --check` | Passed |

The sample and demo counts, rules, UTC triggers, and evidence lines match the
independent tables in `samples/README.md`. The suspicious demo includes the
inclusive 300/600-second boundaries, repeated qualifying successes, unrelated
out-of-order input, and rearming when evidence expires during a silent gap.

Verification scope at implementation: Codex tested Windows/Python 3.14.6 only.
The later independent Phase 2 review below verifies Linux/Python 3.12.14.
Python 3.11 remains unverified. Events and evidence are retained in memory;
large-log performance has not been benchmarked. Fixed rules are investigation
heuristics, not proof of compromise. Console output includes full source log
text and can be lengthy. IDs are source-scoped rather than globally unique.
Permission denial remains mock-tested. Configuration, JSON export, dashboard,
database, and external integrations were not implemented.

GitHub CLI was found at `C:\Program Files\GitHub CLI\gh.exe` and is
authenticated as `rujiraji`; it is absent from this process's PATH and is
invoked by its absolute path. That terminal CLI created PR #2 into `main`.
The owner reviews, accepts, and merges it; Codex stops at the phase boundary.

## Phase 2 acceptance and independent review

The owner accepted Phase 2 based on independent review of commit
`4b51f8e998a6dfe193d2a95000859ee382c83342`, PR #2. These results were reported
by the owner and are separate from checks run by Codex:

- Linux, Python 3.12.14: all 69 tests passed.
- Sample, normal, suspicious, and help commands passed.
- All five suspicious findings matched documented triggers and supporting evidence.
- An independent reference calculation matched 400 generated datasets of 180 events each, covering triggers, evidence, ordering, IDs, metadata, repeatability, and input preservation.
- No blocking issues were found. Python 3.11 and large-log performance remain unverified.

## Phase 2 acceptance-handoff checks by Codex

On 2026-10-14, Codex verified the actual Git checkout's repository root and
`origin` pointing to `https://github.com/rujiraji/LoginWatch.git`. The working tree was
clean on `phase-2-detection`; `HEAD` and `origin/phase-2-detection` matched the
reviewed commit. `git diff 4b51f8e998a6dfe193d2a95000859ee382c83342 --` was empty
before documentation edits. No implementation or unrelated work was changed.

Checks run by Codex on Windows, Python 3.14.6:

| Exact command | Result |
| --- | --- |
| `python --version` | `Python 3.14.6`, exit 0 |
| `python -m unittest discover -s tests` | 69 tests passed, exit 0 |
| `python loginwatch.py samples/sample.log` | Exit 0; original counts unchanged, zero findings |
| `python loginwatch.py samples/normal.log` | Exit 0; 8 events, 6 successes, 2 failures, 3 IPs, 3 usernames, no blank/skipped lines, zero findings |
| `python loginwatch.py samples/suspicious.log` | Exit 0; 14 events, 3 successes, 11 failures, 3 IPs, 7 usernames, no blank/skipped lines, five findings matching documented triggers and evidence |
| `python loginwatch.py --help` | Exit 0 |
| `git diff --check` | Passed |
| `git fetch origin` | Completed successfully; `origin/main` remained at Phase 1 merge commit `357ea3e18e7684944e63bfc7d81d8469ab974a84` |

The authenticated terminal's GitHub CLI confirmed
`https://github.com/rujiraji/LoginWatch/pull/2` was OPEN with no merge timestamp.
At that handoff, PR #2 was ready for the owner's merge; Codex did not merge it
or begin Phase 3. The owner has since merged it; the Phase 3 record follows.

## Phase 3 implementation and verification

On 2026-10-15, the authenticated terminal's `gh` CLI confirmed PR #2 was
MERGED at `f179620ddd0adefde9432051b362f46633db326e`. The checkout was clean on
`phase-2-detection`, with the correct `origin` URL. Codex switched to `main`,
ran `git pull --ff-only origin main`, and verified the merge. No local or
remote `phase-3-reports` branch existed; a new branch was created from updated
`main`. No repository was initialized and no user work was overwritten.

Before implementation, SPEC defined the exact versioned JSON structure,
byte formatting, integer bounds, and atomic-export/path-protection contracts.

Changed components and flow:

- `configuration.py`: strict UTF-8 JSON loading with duplicate/non-finite rejection, explicit validation of all six fields, positive 32-bit bounds, and frozen effective configuration. The CLI loads this before parsing input.
- `analyzer.py`: receives immutable effective configuration, preserves default detection semantics, and records/explains the actual count/window thresholds in every finding. Parsing remains independent and unchanged.
- `reporter.py`: serializes schema 1.0 with all summary, configuration, finding, and supporting-event fields; metadata timestamps are UTC with `Z` and raw text is preserved. Stable keys/indentation/LF encoding omit generated or machine-specific data. Console no-findings wording refers to the three rules, including custom settings.
- `report_export.py`: protects input/configuration aliases by resolved path and existing-file identity, writes/flushes/fsyncs a temporary file in the destination directory, closes it, and atomically replaces the destination. Failures preserve the existing report and clean up temporary files.
- `loginwatch.py`: coordinates `--config` and `--json`, preserves console reporting on success, and emits concise nonzero-status errors without partial output on configuration/export failure.
- `samples/custom.log`, `samples/custom-config.json`, and `samples/README.md`: a synthetic demo with independently specified counts and exact trigger/evidence membership for all three custom thresholds. The same log stays quiet under defaults.
- `tests/`: configuration types/limits/duplicates/errors, each configurable rule and boundaries, complete JSON schema/evidence/UTC/order/repeatability, CLI validation/export failures, path aliases, existing-file preservation, and simulated partial-write/fsync/replace failures. Previous parser/summary/detection behavior is retained.
- README, SPEC, and PLAN: usage, schema, safety/replacement policy, data sensitivity, verification, and Phase 3 status. `.gitignore` ignores only the two generated demo report filenames in addition to existing Python cache entries.

Verification by Codex: Windows PowerShell, Python 3.14.6, standard library only.

| Exact command | Result |
| --- | --- |
| `python -m unittest discover -s tests` | `Ran 138 tests`; `OK (skipped=6)`, exit 0 |
| `python loginwatch.py samples/sample.log` | Exit 0; 9 events, 4 successes, 5 failures, 3 IPs, 5 usernames, 2 blank lines, 4 skipped lines, zero findings |
| `python loginwatch.py samples/normal.log` | Exit 0; 8 events, 6 successes, 2 failures, 3 IPs, 3 usernames, no blank/skipped lines, zero findings |
| `python loginwatch.py samples/suspicious.log` | Exit 0; 14 events, 3 successes, 11 failures, 3 IPs, 7 usernames, no blank/skipped lines, five findings |
| `python loginwatch.py samples/custom.log` | Exit 0; 5 events, 1 success, 4 failures, 2 IPs, 3 usernames, no blank/skipped lines, zero findings |
| `python loginwatch.py samples/custom.log --config samples/custom-config.json --json custom-report.json` | Exit 0; same summary, three findings and full schema 1.0 export matching independent fixture expectations |
| `python loginwatch.py samples/suspicious.log --json suspicious-report.json` | Exit 0; same summary/five findings as without export, full schema 1.0 export |
| `python loginwatch.py --help` | Exit 0; input, configuration, and JSON export options |
| `git diff --check` | Passed |
| `py --list-paths` | Only 3.14 runtimes listed |
| `py -3.11 --version` | Exit 1: no matching runtime installed; no Python version was installed for this task |

The original sample, normal, suspicious, and custom demo results match the
independent fixture tables in `samples/README.md`. Tests compare JSON bytes
across separate processes, output destinations, and equivalent source path
spellings, and verify complete evidence and effective thresholds. An initial
test incorrectly assumed a decoder recursion limit common to all Python
versions; it now accepts either documented decoding or root-validation errors,
with a separate check for converting decoder recursion errors cleanly.

Local verification limitations: six symlink cases were skipped because this
Windows session cannot create symlinks (confirmed `WinError 1314`, required
privilege absent).
Hard-link collision cases passed locally. The later independent Phase 3
review below passed all 138 tests without skips on Linux/Python 3.12.14,
including symlink and hard-link protection. Python 3.11 is unavailable here
and remains unverified, as does large-log performance. Events, findings, and
JSON serialization remain in memory. Disk-full, permission, and replacement failures include mock
tests alongside real missing-path, directory, encoding, and hard-link cases.
Atomic replacement does not coordinate with concurrent filesystem changes or
guarantee directory-entry crash durability. Reports retain usernames and raw
log text; IDs remain scoped to source records/line numbers. No dashboard,
database, integrations, or Phase 4 work was added.

At implementation handoff, Phase 3 was Implemented — awaiting review. Codex
pushed `phase-3-reports` and opened PR #3 using the authenticated terminal's
`gh` CLI, then stopped. Owner acceptance and the subsequent checks follow;
Codex has not merged it or begun Phase 4.

## Phase 3 acceptance and independent review

The owner accepted Phase 3 based on independent review of commit
`16751333a60bec6f93ec6568a46ecefb08d63966`, PR #3. These results were reported
by the owner, separately from checks run by Codex:

- Linux, Python 3.12.14: all 138 tests passed with no skips.
- Symlink and hard-link protection tests passed.
- All seven documented demo/help commands passed.
- Both JSON reports matched independently checked summaries, rules, thresholds, and supporting source lines.
- Repeated exports produced identical bytes.
- Source files remained unchanged and no temporary export files remained.
- No blocking issues were found. Python 3.11 and large-log performance remain unverified.

## Phase 3 acceptance-handoff checks by Codex

On 2026-10-15, Codex verified the current repository root and `origin` URL
for `https://github.com/rujiraji/LoginWatch`. Before documentation edits,
the working tree was clean on `phase-3-reports`; `HEAD` and
`origin/phase-3-reports` pointed to the reviewed commit, and
`git diff 16751333a60bec6f93ec6568a46ecefb08d63966 --` was empty.
No implementation or unrelated work was changed.

Checks run by Codex on Windows, Python 3.14.6:

| Exact command | Result |
| --- | --- |
| `python --version` | `Python 3.14.6`, exit 0 |
| `python -m unittest discover -s tests` | `Ran 138 tests`; `OK (skipped=6)`, exit 0; symlink creation remains unavailable in this Windows session |
| `python loginwatch.py samples/sample.log` | Exit 0; 9 events, 4 successes, 5 failures, 3 IPs, 5 usernames, 2 blank lines, 4 skipped lines, zero findings |
| `git diff --check` | Passed |
| `git fetch origin` | Completed successfully; `origin/main` remained at Phase 2 merge commit `f179620ddd0adefde9432051b362f46633db326e` |

The authenticated terminal's `gh` CLI confirmed
`https://github.com/rujiraji/LoginWatch/pull/3` was OPEN with no merge timestamp.
At that handoff, PR #3 was ready for the owner's merge. Codex stopped without
merging it, beginning Phase 4, creating tags, or publishing a GitHub release.
The owner has since merged it; the Phase 4 record follows.

## Phase 4 delivery implementation and verification

On 2026-10-15, `gh` confirmed PR #3 was MERGED at
`5e7c9cac31e8ea21d581a71ab80c1abbf2c14adc`. The actual checkout was clean on
`phase-3-reports` with `origin` pointing to `https://github.com/rujiraji/LoginWatch.git`.
Codex switched to `main` and ran `git pull --ff-only origin main`, which
fast-forwarded to the merge. No local or remote `phase-4-delivery` branch
existed; it was created from updated `main` without resetting user work.

Delivered artifacts:

- README is a concise entry point; historical verification remains in this file.
- `docs/WALKTHROUGH.md` explains the quiet normal demo, five suspicious findings, default/custom behavior, full JSON evidence, and repeatability checks.
- `docs/ARCHITECTURE.md` maps components and inputs/outputs and supplies interview prompts on inclusive windows, ordering, episode rearming, deterministic bytes, atomic export, and limits.
- `docs/RELEASE_NOTES.md` is a proposed first-release description; `docs/PORTFOLIO.md` distinguishes owner requirements/design/review from Codex-assisted implementation and proposes accurate résumé wording without usage/impact/performance claims.
- `scripts/verify_demo.py` drives all seven CLI demo/help commands plus two repeat exports, independently checks documented summaries/findings/thresholds/full supporting records, and checks byte equality, source preservation, and temporary-file cleanup. Its reports use a temporary directory; existing checkout reports are left alone.
- `.github/workflows/tests.yml` runs verbose unittest on the Python 3.11/3.14 × Ubuntu/Windows matrix for PRs into `main` and pushes to `main`, with read-only repository permissions and no application package install. Action versions follow the official [checkout](https://github.com/actions/checkout) and [setup-python](https://github.com/actions/setup-python) usage; actual CI evidence is recorded after execution.

Runtime modules, existing tests, and fixtures are unchanged from accepted
Phase 3. No dashboard, database, integration, packaging framework, tag, or
published release was added. Documentation writing used the HumanWriting
skill to keep claims specific and contribution disclosure accurate.

### Fresh-checkout results

Codex cloned `phase-4-delivery` from GitHub into a new temporary directory using
`git clone --branch phase-4-delivery https://github.com/rujiraji/LoginWatch.git LoginWatch-demo`.
The clone was clean at `76b5f3bc1f38e4094de75b5fe6d00f8230e82061`.
A separate `python -m venv --without-pip` environment used Python 3.14.6 on
Windows. `importlib.metadata.distributions()` returned an empty list; no
third-party packages were installed. The commands below used that environment's
Python executable from the clone root, shown as `python` for readability.

| Command | Observed result |
| --- | --- |
| `python --version` | Python 3.14.6 |
| `python -m unittest discover -s tests` | `Ran 138 tests`; `OK (skipped=6)`, exit 0; local Windows symlink privilege unavailable |
| `python loginwatch.py samples/sample.log` | Exit 0; 9 events, 4 successes, 5 failures, 3 IPs, 5 usernames, 2 blank lines, 4 skipped lines, zero findings |
| `python loginwatch.py samples/normal.log` | Exit 0; 8 events, 6 successes, 2 failures, 3 IPs, 3 usernames, no blank/skipped lines, zero findings |
| `python loginwatch.py samples/suspicious.log` | Exit 0; 14 events, 3 successes, 11 failures, 3 IPs, 7 usernames, no blank/skipped lines, five expected findings |
| `python loginwatch.py samples/custom.log` | Exit 0; 5 events, 1 success, 4 failures, 2 IPs, 3 usernames, no blank/skipped lines, zero findings |
| `python loginwatch.py samples/custom.log --config samples/custom-config.json --json custom-report.json` | Exit 0; same summary, three expected findings and full report |
| `python loginwatch.py samples/suspicious.log --json suspicious-report.json` | Exit 0; same summary/five findings and full report |
| `python loginwatch.py --help` | Exit 0; positional input, `--config`, and `--json` help |
| `python scripts/verify_demo.py` | Exit 0; all seven demo/help commands and two repeat exports passed |
| `git status --porcelain=v1` in the clone after verification | Empty; only ignored caches/demo reports were generated |
| `git diff --check` | Passed |

The verifier checked every summary count, ordered rule/ID/trigger, actual
threshold, full evidence membership/raw record, and UTC metadata against
fixed expectations from `samples/README.md`. Both exports repeated with
identical bytes. Sources/configuration stayed unchanged and no temporary export
files remained. The two reports created by the literal documented commands in
the clone were also checked against the verifier's independent expectations.
Local Markdown target checks found no missing relative file links.

### Observed GitHub Actions results

[CI run 38804423752](https://github.com/rujiraji/LoginWatch/actions/runs/38804423752)
for PR #4, associated with branch head
`76b5f3bc1f38e4094de75b5fe6d00f8230e82061`, completed successfully. Codex read
the job results and logs via the authenticated terminal's `gh` CLI:

| Matrix job | Reported interpreter | Unittest result | Skips |
| --- | --- | --- | --- |
| ubuntu-latest / Python 3.11 | 3.11.17 | 138 tests, OK | 0 |
| ubuntu-latest / Python 3.14 | 3.14.8 | 138 tests, OK | 0 |
| windows-latest / Python 3.11 | 3.11.9 | 138 tests, OK | 0 |
| windows-latest / Python 3.14 | 3.14.8 | 138 tests, OK | 0 |

The exact CI command was `python -m unittest discover -s tests -v`, preceded
by `python --version`. No application package installation step was used.
Both hosted platforms permitted link creation; symlink/hard-link tests passed.
Python 3.11 is now verified in these observed CI environments. Earlier
references to it being unverified describe the evidence available at those
phase boundaries. The local Windows six-skip result remains a separate host
limitation, not a skipped CI check. Subsequent documentation-only commits can
produce additional runs; consult PR #4 for checks on its latest head.

### Review boundary and remaining limits

PR #4 prepares a reviewable delivery candidate. Phase 4 is **Implemented —
awaiting review**. Only the owner may accept or merge it. No tag, GitHub release,
or final acceptance was created or claimed by Codex.

Runtime modules, existing tests, and fixtures remain unchanged from the
accepted Phase 3 baseline, confirmed with `git diff --name-only main --` for
those paths. Large-log performance is unverified; memory usage and verbose
evidence output are unchanged. The input grammar is narrow and rules are
investigation heuristics. Reports retain usernames/raw text, IDs depend on
source lines, and atomic export does not coordinate concurrent filesystem
changes or guarantee directory-entry crash durability. Fresh-checkout demos
were exercised locally on Windows 3.14.6; CI ran the unittest suite, not the
separate demo verifier. Independent reviews supplied by the owner remain
distinct from the Codex and CI results above.
