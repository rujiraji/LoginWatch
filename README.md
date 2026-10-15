# LoginWatch

A Python command-line tool for reviewing SSH password-login logs and explaining suspicious login patterns with supporting evidence.

## Current status

Phase 1 is **Accepted**, following owner-reported independent review of commit
`aaa183c0adfe37a734a5431bf8b1db51b930ce22`. Phase 2 is **Accepted**, following
owner-reported independent review of commit
`4b51f8e998a6dfe193d2a95000859ee382c83342` in PR #2. The CLI parses the
documented SSH password-login format, prints the
activity summary, and explains findings from three default detection rules.
Configuration and JSON export remain planned. See [docs/PLAN.md](docs/PLAN.md)
for phase status.

## Purpose

Turn a log file into an accurate activity summary and an evidence-backed
console report. Findings are investigation signals, not proof of compromise.
This portfolio project records the owner's requirements, design
decisions, and phase review, alongside Codex-assisted implementation and tests.

## Architecture

Log file → parser → events and line counts → analyzer → findings → reporter
→ console. The CLI coordinates parsing, summary calculation, detection, and
formatting; it completes input reading before printing any report.

- `loginwatch.py`: accepts an input path, calls parsing and reporting, and returns an exit status.
- `models.py`: immutable `LoginEvent`, `ParseResult`, `ActivitySummary`, and `Finding` data models.
- `parser.py`: reads UTF-8 without changing the file; returns validated events in source order, blank-line counts, and skipped-line counts. Events retain UTC timestamps, normalized IPs, usernames, results, line numbers, and raw text.
- `analyzer.py`: accepts parsed events, analyzes a view sorted by UTC timestamp and source line, and returns ordered findings with explanations, thresholds, and immutable evidence snapshots. It does not alter events or source ordering.
- `reporter.py`: calculates the seven summary counts and formats the summary and findings, including each supporting source line and original event text.
- `samples/`: synthetic parsing, normal, and suspicious fixtures with independent expected counts and findings.
- `tests/`: standard-library parser, summary, detection, and CLI checks.

Findings retain source log text and usernames in memory and display them on
the console; handle the report with the same care as its input logs.

## Setup and usage

Python 3.11+; standard library only. No package installation is required.
Run these commands from the repository directory:

```bash
python loginwatch.py samples/sample.log
python loginwatch.py samples/normal.log
python loginwatch.py samples/suspicious.log
python -m unittest discover -s tests
python loginwatch.py --help
```

The CLI exits 0 after a completed report, including empty files, skipped
records, or findings. Input errors exit 1 with a concise error on stderr; invalid CLI usage
exits 2. Missing paths, unreadable files, and invalid UTF-8 do not produce a
partial summary.

Phase 3 will add optional configuration and report export (unavailable now):

```bash
python loginwatch.py samples/sample.log --config config.json --json report.json
```

## Supported input

One SSH password-login event per line with an ISO 8601 timestamp containing year and timezone. This is a deliberately narrow documented format; it does not support every Linux SSH log variant. Examples and exact behavior are in docs/SPEC.md.

## Verified sample output

`python loginwatch.py samples/sample.log` produces:

```text
LoginWatch activity summary
Parsed events: 9
Successful logins: 4
Failed logins: 5
Unique IPs: 3
Unique usernames: 5
Ignored blank lines: 2
Skipped nonblank lines: 4

Findings: 0
No suspicious patterns detected by the three default rules.
```

The fixture has 15 lines: 9 supported events, 2 blank lines, and 4 malformed or
unsupported records. [samples/README.md](samples/README.md) specifies each
line's expected outcome, IPs, and usernames. Equivalent IPv6 spellings count
as one IP; `alice` and `Alice` count as different usernames. Duplicate records
remain separate observations. Only parsed events contribute to unique counts.

## Detection and demos

| Rule | Fixed Phase 2 trigger |
| --- | --- |
| repeated_failures | At least five failures from one IP within 300 seconds |
| success_after_failures | A success preceded by at least five failures for the same IP and case-sensitive username within 600 seconds |
| multiple_accounts | Failures involving at least five distinct usernames from one IP within 600 seconds |

Windows include both endpoints. Equal timestamps use source line numbers to
decide whether a failure precedes a success. Repeated-failure and multiple-account
episodes suppress additional findings while qualifying evidence remains at or above
threshold. Expiry ends an episode even during a silent gap; old evidence is
expired before adding a new failure, which can immediately start a new episode.
Each qualifying success produces its own finding. Each finding freezes the
complete matching evidence window at its trigger.

`python loginwatch.py samples/normal.log` prints 8 events, 6 successes,
2 failures, 3 IPs, 3 usernames, no blank/skipped lines, and zero findings.

`python loginwatch.py samples/suspicious.log` prints 14 events, 3 successes,
11 failures, 3 IPs, 7 usernames, no blank/skipped lines, and five findings:

| Rule | Trigger line | Evidence lines |
| --- | --- | --- |
| repeated_failures | 5 | 1, 2, 3, 4, 5 |
| success_after_failures | 6 | 1, 2, 3, 4, 5, 6 |
| success_after_failures | 7 | 1, 2, 3, 4, 5, 7 |
| multiple_accounts | 13 | 9, 10, 11, 12, 13 |
| multiple_accounts | 14 | 10, 11, 12, 13, 14 |

[samples/README.md](samples/README.md) explains each trigger independently.
The console shows stable finding IDs, rule names, UTC trigger/evidence times,
IPs, usernames, thresholds, explanations, and supporting source lines.
For example, the first finding explains: `5 failed password logins from
192.0.2.10 occurred within 300 seconds (threshold: 5 failures).`

## Limitations

Offline summaries and deterministic heuristic findings. Configuration and
report export are unavailable. The supported format requires a year, timezone, host,
`sshd[PID]`, and the exact documented password message. Traditional syslog
timestamps and public-key authentication are skipped. Files must be UTF-8;
invalid encoding is an error. Events are held in memory, so very large logs
are not a streaming workflow. Python 3.11 is the minimum target; verification
for Phase 2 was performed by Codex on Python 3.14.6 on Windows and independently
on Python 3.12.14 on Linux. Python 3.11 and large-log performance remain
unverified. The independent review evidence is recorded separately below.

No live monitoring, blocking, threat-intelligence lookup, or account
remediation. A shared IP can represent multiple people, and missing logs can
hide activity. Detection thresholds express heuristics rather than established
proof of an attack. Finding IDs are stable for the same source records and
line numbers, not globally unique across files. Inserting or moving source
lines can change IDs. All matching evidence is printed, so dense logs can
produce lengthy console reports. Large-log performance has not been benchmarked.

## Project documents

- docs/SPEC.md: scope, data contracts, rules, and report behavior.
- docs/PLAN.md: phases and acceptance criteria.
- AGENTS.md: repository instructions for Codex.

## Delivery evidence

Original implementation verification by Codex on Windows with Python 3.14.6:

- `python -m unittest discover -s tests`: 27 tests passed, exit 0.
- `python loginwatch.py samples/sample.log`: exit 0; the original seven summary counts match the independently documented fixture expectations above.
- `python --version`: `Python 3.14.6`.

Permission-denied handling is tested with a mock; missing-file, directory,
invalid-encoding, and other CLI behavior are tested through subprocesses.
The original implementation workspace lacked Git metadata, so Git status/diff
checks were unavailable at that time. This was a historical workspace
limitation. The current workspace is the Git checkout for
`https://github.com/rujiraji/LoginWatch`, with `origin` pointing to that repository.

Independent review reported by the owner (separate from Codex's checks):

- Reviewed commit: `aaa183c0adfe37a734a5431bf8b1db51b930ce22`.
- Linux, Python 3.12.14: all 27 tests passed and sample output matched expectations.
- Additional checks passed for a 120-event dataset, timezone boundaries, and invalid UTF-8 after valid data.
- No blocking issues were found; the owner accepted Phase 1. Python 3.11 remains unverified.

Codex acceptance-handoff checks on 2026-10-14, Windows, Python 3.14.6:

- Confirmed the repository root, `origin` URL, and clean working tree; the implementation matched the reviewed commit exactly before documentation changes.
- `python -m unittest discover -s tests`: 27 tests passed, exit 0.
- `python loginwatch.py samples/sample.log`: exit 0; the seven summary counts matched the documented expectations above.
- After `git fetch origin`, `origin/main` was still at planning commit `2f3759d168b4972dd072618a5945d2d8f1af1415`; Phase 1 had not been merged.

The owner subsequently merged Phase 1 via PR #1 at commit
`357ea3e`. Phase 2 work began from that merged baseline after a
fast-forward-only pull and inspection/fast-forward of the existing branch.

Phase 2 verification by Codex on 2026-10-14, Windows, Python 3.14.6:

- `python -m unittest discover -s tests`: 69 tests passed, exit 0.
- `python loginwatch.py samples/sample.log`: exit 0; exact current output above, including zero findings.
- `python loginwatch.py samples/normal.log`: exit 0; counts documented above, zero findings.
- `python loginwatch.py samples/suspicious.log`: exit 0; counts and all five findings match the independent expectation table in samples/README.md.
- `python loginwatch.py --help`: exit 0; describes the summary, detection, and UTF-8 input.
- `git diff --check`: passed.

Independent Phase 2 review reported by the owner (not checks run by Codex):

- Reviewed commit: `4b51f8e998a6dfe193d2a95000859ee382c83342`, PR #2.
- Linux, Python 3.12.14: all 69 tests and the sample, normal, suspicious, and help commands passed.
- All five suspicious findings matched the documented triggers and supporting evidence.
- An independent reference calculation matched 400 generated datasets of 180 events each, covering triggers, evidence, ordering, IDs, metadata, repeatability, and input preservation.
- No blocking issues were found; the owner accepted Phase 2. Python 3.11 and large-log performance remain unverified.

Codex Phase 2 acceptance-handoff checks on 2026-10-14, Windows, Python 3.14.6:

- Verified the actual repository root and `origin` URL; the clean `phase-2-detection` checkout and remote branch matched the reviewed commit before documentation changes.
- `python -m unittest discover -s tests`: 69 tests passed, exit 0.
- `python loginwatch.py samples/sample.log`: exit 0; original counts, zero findings.
- `python loginwatch.py samples/normal.log`: exit 0; documented counts, zero findings.
- `python loginwatch.py samples/suspicious.log`: exit 0; documented counts and five findings with the expected evidence.
- `python loginwatch.py --help`: exit 0.
- `git diff --check`: passed.

PR #2 is ready for the owner to merge. Phase 3 has been assigned conditionally
on that merge; implementation stops here while PR #2 remains unmerged.
