# LoginWatch

A Python command-line tool for reviewing SSH password-login logs and explaining suspicious login patterns with supporting evidence.

## Current status

Phase 1 is **Accepted**, following owner-reported independent review of commit
`aaa183c0adfe37a734a5431bf8b1db51b930ce22`. The CLI parses the documented SSH
password-login format and prints an activity summary. Detection, configuration,
and JSON export remain planned. See [docs/PLAN.md](docs/PLAN.md) for phase status.

## Purpose

Turn a log file into an accurate activity summary. Later phases will add an
evidence-backed report; findings will be investigation signals, not proof of
compromise. This portfolio project records the owner's requirements, design
decisions, and phase review, alongside Codex-assisted implementation and tests.

## Architecture

Phase 1: log file → parser → login events and line counts → reporter → console.
The CLI coordinates these components.

- `loginwatch.py`: accepts an input path, calls parsing and reporting, and returns an exit status.
- `models.py`: immutable `LoginEvent`, `ParseResult`, and `ActivitySummary` data models.
- `parser.py`: reads UTF-8 without changing the file; returns validated events in source order, blank-line counts, and skipped-line counts. Events retain UTC timestamps, normalized IPs, usernames, results, line numbers, and raw text.
- `reporter.py`: turns a `ParseResult` into an `ActivitySummary`, then formats the seven counts as console text.
- `samples/`: a synthetic fixture and independently specified line-by-line expectations.
- `tests/`: standard-library parser, summary, and CLI checks.

Phase 2 will introduce `analyzer.py` and findings between parsing and reporting.

## Setup and usage

Python 3.11+; standard library only. No package installation is required.
Run these commands from the repository directory:

```bash
python loginwatch.py samples/sample.log
python -m unittest discover -s tests
python loginwatch.py --help
```

The CLI exits 0 after a completed summary, including empty files or skipped
records. Input errors exit 1 with a concise error on stderr; invalid CLI usage
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
```

The fixture has 15 lines: 9 supported events, 2 blank lines, and 4 malformed or
unsupported records. [samples/README.md](samples/README.md) specifies each
line's expected outcome, IPs, and usernames. Equivalent IPv6 spellings count
as one IP; `alice` and `Alice` count as different usernames. Duplicate records
remain separate observations. Only parsed events contribute to unique counts.

## Limitations

Offline activity summaries only; no detection rules, configuration, or report
export in Phase 1. The supported format requires a year, timezone, host,
`sshd[PID]`, and the exact documented password message. Traditional syslog
timestamps and public-key authentication are skipped. Files must be UTF-8;
invalid encoding is an error. Events are held in memory, so very large logs
are not a streaming workflow. Python 3.11 is the minimum target; verification
was performed on Python 3.14.6 on Windows and independently on Python 3.12.14
on Linux. Python 3.11 remains unverified.

No live monitoring, blocking, threat-intelligence lookup, or account
remediation. A shared IP can represent multiple people, and missing logs can
hide activity. Future detection thresholds will express heuristics rather
than established proof of an attack.

## Project documents

- docs/SPEC.md: scope, data contracts, rules, and report behavior.
- docs/PLAN.md: phases and acceptance criteria.
- AGENTS.md: repository instructions for Codex.

## Delivery evidence

Original implementation verification by Codex on Windows with Python 3.14.6:

- `python -m unittest discover -s tests`: 27 tests passed, exit 0.
- `python loginwatch.py samples/sample.log`: exit 0; exact output above matches the independently documented fixture expectations.
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
- `python loginwatch.py samples/sample.log`: exit 0; output matched the verified output above.
- After `git fetch origin`, `origin/main` was still at planning commit `2f3759d168b4972dd072618a5945d2d8f1af1415`; Phase 1 had not been merged.

Phase 2 implementation waits for the owner to merge the Phase 1 PR into `main`.
