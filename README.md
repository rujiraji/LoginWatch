# LoginWatch

A Python command-line tool for reviewing SSH password-login logs and explaining suspicious login patterns with supporting evidence.

## Current status

Phase 1 is **Accepted**, following owner-reported independent review of commit
`aaa183c0adfe37a734a5431bf8b1db51b930ce22`. Phase 2 is **Accepted**, following
owner-reported independent review of commit
`4b51f8e998a6dfe193d2a95000859ee382c83342` in PR #2. The CLI parses the
documented SSH password-login format, prints the
activity summary, and explains findings from three detection rules. Phase 3
configuration and JSON export are **Accepted**, following owner-reported
independent review of commit `16751333a60bec6f93ec6568a46ecefb08d63966` in PR #3.
See [docs/PLAN.md](docs/PLAN.md) for phase status.

## Purpose

Turn a log file into an accurate activity summary and an evidence-backed
console report and optional reproducible JSON export. Findings are
investigation signals, not proof of compromise.
This portfolio project records the owner's requirements, design
decisions, and phase review, alongside Codex-assisted implementation and tests.

## Architecture

Log file → parser → events and line counts → analyzer → findings → reporter
→ console. The CLI coordinates parsing, summary calculation, detection, and
formatting. Configuration is validated first; reading, analysis, and any JSON
export complete before console reporting.

- `loginwatch.py`: coordinates the input path, optional configuration/export, parsing, analysis, reporting, and exit status.
- `configuration.py`: loads strict UTF-8 JSON and validates the frozen `DetectionConfig`, filling omitted fields with defaults.
- `models.py`: immutable `LoginEvent`, `ParseResult`, `ActivitySummary`, and `Finding` data models.
- `parser.py`: reads UTF-8 without changing the file; returns validated events in source order, blank-line counts, and skipped-line counts. Events retain UTC timestamps, normalized IPs, usernames, results, line numbers, and raw text.
- `analyzer.py`: accepts events and immutable effective configuration, analyzes a view sorted by UTC timestamp and source line, and returns ordered findings with actual thresholds and immutable evidence snapshots. It does not alter events or source ordering.
- `reporter.py`: calculates summary counts and formats console text and schema 1.0 JSON with every finding field and complete supporting events.
- `report_export.py`: checks source/configuration path collisions and writes UTF-8 using a temporary file and atomic replacement.
- `samples/`: synthetic parsing, normal, suspicious, and custom-threshold fixtures with independent expected counts and findings.
- `tests/`: standard-library parser, configuration, summary, detection, export, and CLI checks.

Console and exported reports retain usernames and raw source log text;
handle and share them with the same care as the input logs.

## Setup and usage

Python 3.11+; standard library only. No package installation is required.
Run these commands from the repository directory:

```bash
python loginwatch.py samples/sample.log
python loginwatch.py samples/normal.log
python loginwatch.py samples/suspicious.log
python loginwatch.py samples/custom.log
python loginwatch.py samples/custom.log --config samples/custom-config.json --json custom-report.json
python loginwatch.py samples/suspicious.log --json suspicious-report.json
python -m unittest discover -s tests
python loginwatch.py --help
```

The CLI exits 0 after a completed report, including empty files, skipped
records, or findings. Input, configuration, and JSON output errors exit 1 with
a concise error on stderr; invalid CLI usage exits 2. Read/validation/export
failures do not print a partial console report. All commands use Python's
standard library; no database, network service, or package install is required.

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
No suspicious patterns detected by the three rules.
```

The fixture has 15 lines: 9 supported events, 2 blank lines, and 4 malformed or
unsupported records. [samples/README.md](samples/README.md) specifies each
line's expected outcome, IPs, and usernames. Equivalent IPv6 spellings count
as one IP; `alice` and `Alice` count as different usernames. Duplicate records
remain separate observations. Only parsed events contribute to unique counts.

## Detection and demos

| Rule | Default trigger (configurable in Phase 3) |
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

## Configuration and custom demo

Use `--config PATH` to load a UTF-8 JSON object. Omitted fields use these defaults;
an empty object is valid:

```json
{
  "repeated_failures_count": 5,
  "repeated_failures_window_seconds": 300,
  "success_after_failures_count": 5,
  "success_after_failures_window_seconds": 600,
  "multiple_accounts_count": 5,
  "multiple_accounts_window_seconds": 600
}
```

All six fields must be integers in **1–2147483647**. This bound keeps time
windows safely representable and portable; counts use the same bound.
Booleans, floats, strings, nonpositive/out-of-range values, unknown fields,
duplicate keys, non-object roots, malformed JSON, and non-finite constants are
rejected. Invalid UTF-8 and unreadable configuration files produce clear errors.
Files are read without modification. Findings explain the thresholds actually
used; the original defaults preserve Phase 2 detection behavior.

`samples/custom.log` has 5 events, 1 success, 4 failures, 2 IPs, 3 usernames,
no blank/skipped lines, and zero findings under defaults.
The documented command using `samples/custom-config.json` changes all counts
to 2 and the windows to 30/60/60 seconds. It produces exactly three findings:

| Rule | Trigger line | Evidence lines | Threshold count/window |
| --- | --- | --- | --- |
| repeated_failures | 2 | 1, 2 | 2 / 30 seconds |
| success_after_failures | 3 | 1, 2, 3 | 2 / 60 seconds |
| multiple_accounts | 5 | 4, 5 | 2 / 60 seconds |

The same command writes `custom-report.json`; independent expected triggers
and evidence are in [samples/README.md](samples/README.md).

## JSON export and file safety

`--json PATH` retains console output and writes schema version `1.0` with the
source basename, all seven summary counts, all six effective configuration
values, and ordered findings. Each finding retains every model field and all
supporting events, including line numbers and raw text. See the exact schema
in [docs/SPEC.md](docs/SPEC.md). Timestamp metadata is UTC with `Z`; original
timestamp spellings remain in raw text.

Equivalent runs produce identical UTF-8 bytes: sorted object keys, two-space
indentation, LF newlines, one trailing LF, no BOM, and no generated timestamps
or machine-specific metadata. Source basename and raw source text are part of
the report; changing either can change bytes. The destination path is not
embedded. The default suspicious export has five findings; the custom export
has the three findings above. Both demo report filenames are ignored by Git.

The destination directory must exist. Successful exports **replace existing
reports** using a temporary file in the destination directory, flush/fsync,
and atomic replacement. Write/sync/replace failures preserve the old report
and remove temporary files. An allowed destination symlink to an unrelated
report is replaced as an entry; its former target is left untouched.
Exports cannot refer to the input log or configuration, including relative
paths, symlinks, or hard links where supported. These checks run before
writing and again before replacement. Source and configuration files are
never written. Atomic replacement does not coordinate with concurrent changes
to the filesystem or guarantee directory-entry crash durability.

Exports retain usernames and raw log text and can expose sensitive data.

## Limitations

Offline summaries, configurable deterministic findings, and JSON reports.
The supported format requires a year, timezone, host,
`sshd[PID]`, and the exact documented password message. Traditional syslog
timestamps and public-key authentication are skipped. Files must be UTF-8;
invalid encoding is an error. Events are held in memory, so very large logs
are not a streaming workflow. Python 3.11 is the minimum target; verification
for Phase 3 was performed by Codex on Python 3.14.6 on Windows and independently
on Python 3.12.14 on Linux. The independent Linux run passed all 138 tests
without skips, including symlink and hard-link protection. Python 3.11 and
large-log performance remain unverified. Creating symlinks is unavailable in
this Windows session, so six symlink cases are still skipped locally;
hard-link tests pass here. This local limitation does not apply to the
independent Linux verification recorded below. Permission, disk-full, and
replacement failures are simulated with mocks alongside real path/error tests.

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
- `python loginwatch.py samples/sample.log`: exit 0; original summary counts and zero findings (Phase 3 later updates the no-findings wording).
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

The owner merged PR #2 at commit `f179620ddd0adefde9432051b362f46633db326e`.
Phase 3 began from that merged baseline after a fast-forward-only pull.

Phase 3 verification by Codex on 2026-10-15, Windows, Python 3.14.6:

- `python -m unittest discover -s tests`: `Ran 138 tests`; `OK (skipped=6)` (symlink creation unavailable).
- All eight commands in Setup and usage were run successfully; sample/normal/default-custom inputs have zero findings, suspicious input has five, and configured custom input has three, matching the independent fixture tables.
- Both JSON export commands preserve console reporting. Tests compare deterministic bytes across separate processes and destination/source path spellings, validate schema/evidence/UTC fields, and check file preservation on failures.
- `py --list-paths` lists only Python 3.14 installations; `py -3.11 --version` exits 1 because no 3.11 runtime is installed. No runtime was installed for this task.
- `git diff --check`: passed.

Independent Phase 3 review reported by the owner (not checks run by Codex):

- Reviewed commit: `16751333a60bec6f93ec6568a46ecefb08d63966`, PR #3.
- Linux, Python 3.12.14: all 138 tests passed without skips, including symlink and hard-link protection tests.
- All seven documented demo/help commands passed.
- Both JSON reports matched independently checked summaries, rules, thresholds, and supporting source lines; repeated exports produced identical bytes.
- Source files remained unchanged and no temporary export files remained.
- No blocking issues were found; the owner accepted Phase 3. Python 3.11 and large-log performance remain unverified.

Codex Phase 3 acceptance-handoff checks on 2026-10-15, Windows, Python 3.14.6:

- Verified the actual repository root and `origin` URL. Before documentation changes, the working tree was clean on `phase-3-reports`, and both `HEAD` and the remote branch matched the reviewed commit exactly.
- `python -m unittest discover -s tests`: `Ran 138 tests`; `OK (skipped=6)`, exit 0. Local symlink creation remains unavailable.
- `python loginwatch.py samples/sample.log`: exit 0; documented summary counts and zero findings.
- `git diff --check`: passed.

PR #3 is ready for the owner to merge. Phase 4 has been assigned conditionally
on that merge; stop here while PR #3 is unmerged. No tags or GitHub releases
have been created by Codex.
