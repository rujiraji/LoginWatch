# LoginWatch walkthrough

This demo uses synthetic logs and documentation IP addresses. Run commands
from the repository root with Python 3.11+; no third-party packages are needed.
For ongoing use, create a separate checkout of `main`:

```bash
git clone --branch main https://github.com/rujiraji/LoginWatch.git LoginWatch-demo
cd LoginWatch-demo
python --version
python -m unittest discover -s tests
```

All four planned phases are Accepted; the project is release-ready and
unpublished. PR #4 still awaits the owner's final merge. Runtime demos work
on current `main`; the delivery documents and `scripts/verify_demo.py` become
available there after that merge. Before then, reviewers can use PR #4's
branch for the complete walkthrough. Test outcomes, environments, and skips
are recorded in [PLAN.md](PLAN.md).

## 1. Establish a quiet baseline

```bash
python loginwatch.py samples/normal.log
```

Expect 8 parsed events, 6 successful logins, 2 failures, 3 IPs, 3 usernames,
no blank/skipped lines, and `Findings: 0`. The two failures concern different
IPs/accounts. Each later success has only one preceding same-account failure,
below the default threshold of five. A quiet report does not prove the log
contains all activity or that an account is secure.

The parsing sample also demonstrates skipped lines and normalization:

```bash
python loginwatch.py samples/sample.log
```

Its exact output is in the [README](../README.md): 9 events, 4 successes,
5 failures, 3 IPs, 5 usernames, 2 ignored blank lines, 4 skipped lines, and
zero findings. IPv6 spellings normalize; usernames remain case-sensitive.

## 2. Explain the five suspicious findings

```bash
python loginwatch.py samples/suspicious.log
```

Expect 14 events, 3 successes, 11 failures, 3 IPs, 7 usernames, no blank/skipped
lines, and `Findings: 5`. All timestamps below are UTC on 2026-10-11.

| Rule / IP | Trigger | Evidence source lines | Why it qualifies |
| --- | --- | --- | --- |
| repeated_failures / 192.0.2.10 | 10:05:00, line 5 | 1, 2, 3, 4, 5 | Five failures within 300 seconds; line 1 is exactly on the boundary |
| success_after_failures / 192.0.2.10 | 10:05:01, line 6 | 1, 2, 3, 4, 5, 6 | A success for alice follows five failures for the same IP/account within 600 seconds |
| success_after_failures / 192.0.2.10 | 10:05:02, line 7 | 1, 2, 3, 4, 5, 7 | A second qualifying success gets its own finding; the first success is not failure evidence |
| multiple_accounts / 198.51.100.20 | 10:30:00, line 13 | 9, 10, 11, 12, 13 | Five distinct usernames have failures within 600 seconds |
| multiple_accounts / 198.51.100.20 | 10:30:01, line 14 | 10, 11, 12, 13, 14 | Line 9 expired during the gap, ending the episode; the new admin failure restores five distinct usernames |

Point to the UTC trigger, the threshold explanation, and the printed original
records with source line numbers. The success findings each have six evidence
records: five failures plus their triggering success. Multiple-account
evidence includes all matching failures, including repeat usernames if present.

Line 8 is unrelated and out of timestamp order. It contributes to the summary
and no finding. Detection sorts a separate view; the original evidence and
source order remain intact. The independent expectations in
[samples/README.md](../samples/README.md) can be checked against the console.

## 3. Change zero findings into three with configuration

```bash
python loginwatch.py samples/custom.log
python loginwatch.py samples/custom.log --config samples/custom-config.json --json custom-report.json
```

Both runs summarize 5 events, 1 success, 4 failures, 2 IPs, 3 usernames, and
no blank/skipped lines. Defaults give zero findings. The configuration changes
the three counts to 2 and their windows to 30, 60, and 60 seconds:

| Rule | Trigger line | Evidence lines | Threshold |
| --- | --- | --- | --- |
| repeated_failures | 2 | 1, 2 | 2 failures in 30 seconds |
| success_after_failures | 3 | 1, 2, 3 | Success after 2 same-IP/account failures in 60 seconds |
| multiple_accounts | 5 | 4, 5 | 2 distinct usernames with failures in 60 seconds |

Every earliest observation is exactly on its relevant boundary. The later
IP's two failures are 60 seconds apart, so they cannot satisfy its 30-second
repeated-failure window. The earlier IP involves only alice, so it cannot
satisfy the multiple-account threshold. The three findings record the actual
thresholds, and the successful event counts as evidence but not as a failure.

## 4. Read and reproduce the JSON report

```bash
python loginwatch.py samples/suspicious.log --json suspicious-report.json
python loginwatch.py --help
python scripts/verify_demo.py
```

The export commands retain console output and replace the two named reports
on success. Open them in a text editor. Each contains `schema_version: "1.0"`,
the source basename, all summary counts, all six effective configuration values,
and ordered findings. Each finding includes its ID, actual thresholds, UTC
metadata, explanation, and full evidence records with source lines and raw text.
The [schema](SPEC.md#json-schema-version-10) defines every field.

The verification script runs all seven CLI demo/help commands in separate
processes, with exports in a temporary directory. It compares each summary
and both JSON evidence sets with fixed fixture expectations, repeats both
exports to compare bytes, checks source preservation, and checks temporary
export cleanup. It leaves existing checkout reports alone. A nonzero exit
means a check failed; it does not replace the unittest suite.

Deterministic output comes from UTC normalization, explicit ordering, stable
JSON formatting, and the absence of generated timestamps. Destination names
do not enter report data. Source text, basename, and line numbers do, so edits
to those inputs can change bytes and IDs. Reports retain usernames and raw log
text; share them with the same care as their source logs.

## 5. Discuss the implementation

Use [ARCHITECTURE.md](ARCHITECTURE.md) to explain the component boundaries,
inclusive windows, rearming before new failures, and atomic export. The
project holds events, evidence, and JSON in memory, and large-log performance
has not been benchmarked. Its supported input format and heuristic thresholds
are deliberate limits, not a claim of general SSH compatibility or confirmed
attack detection.
