# LoginWatch specification

Status: design baseline, version 0.1. Phase 1 input, events, activity summary,
and positional-path CLI are Accepted following owner-reported independent
review of commit `aaa183c0adfe37a734a5431bf8b1db51b930ce22`. Detection (Phase 2)
and configuration/JSON export (Phase 3) are planned, not implemented.

## Goal and user workflow

A user supplies a local SSH log file. LoginWatch parses supported events, summarizes activity, identifies configured suspicious patterns, and reports the evidence behind each finding. Successful delivery means another person can reproduce the sample results using the README.

## First-release scope

Planned first release: Python CLI, one documented password-login format, IPv4
and IPv6, three detection rules, configurable thresholds, console output, JSON
export, synthetic fixtures, meaningful tests, and a repeatable demo. Phase 1
delivers parsing and console summary only.

Out of scope: dashboard, database, email or chat alerts, real-time collection, automatic blocking, external intelligence services, arbitrary log formats, and machine learning. PT/PERSTAT automation is a separate project.

## Input contract

UTF-8 text, one event per line. Supported examples:

```text
2026-10-11T10:00:00-05:00 server sshd[1234]: Failed password for alice from 192.0.2.10 port 54321 ssh2
2026-10-11T10:01:00-05:00 server sshd[1235]: Failed password for invalid user admin from 192.0.2.10 port 54322 ssh2
2026-10-11T10:02:00-05:00 server sshd[1236]: Accepted password for alice from 192.0.2.10 port 54323 ssh2
```

- Require a valid ISO 8601 timestamp with numeric timezone offset or Z. Normalize timestamps to UTC internally.
- The implemented timestamp spelling is `YYYY-MM-DDTHH:MM:SS`, optionally followed by a decimal fractional second, then uppercase `Z` or a numeric offset `±HH:MM` / `±HHMM`. Hours are 00–23; minutes and seconds are 00–59. Offset hours are 00–23 and offset minutes 00–59. Calendar dates must be valid and UTC conversion must fit Python's datetime range. Fractions are stored with microsecond precision; additional fractional digits are truncated.
- Validate IP addresses; support IPv4 and IPv6 and normalize their textual representation.
- IPv6 interface zone identifiers such as `%local` are unsupported; the IP token must be a plain address.
- Extract username as one non-whitespace token. `invalid user admin` means username `admin`.
- Result is success or failure; accept the two message forms above plus Accepted password for a regular user. Failed password supports regular and invalid users.
- Validate the message structure and port as an integer in 1–65535.
- Require a non-whitespace host token and `sshd[PID]:` with an ASCII decimal PID. Timestamp/host/process separators may contain whitespace; password-message separators are literal single spaces as shown above. Leading/trailing whitespace is allowed. No extra message suffix is supported.
- Blank lines are ignored. Other unsupported or malformed lines are skipped and counted once.
- Preserve source line number and original event text for evidence. Identical records on different lines remain separate observations.
- Line numbers start at 1 and include blank/skipped lines. Raw event text excludes the line-ending characters but retains other original spacing. Phase 1 retains source order rather than sorting events.
- Read files without modifying them. Unreadable files and invalid UTF-8 produce a clear error and nonzero exit status.
- Empty files and files with no supported events produce zero event counts and a skipped-line count as applicable.

## Event contract

LoginEvent contains timestamp (timezone-aware UTC), normalized IP, username, result, source line number, and raw line. Host, PID, and port need not be persisted in version 1. Unique counts use only successfully parsed events; usernames are case-sensitive.

## Activity summary

Report parsed events, successful logins, failed logins, unique IPs, unique usernames, ignored blank lines, and skipped nonblank lines. Parsed events must equal successes plus failures. Summaries must match known fixture counts.

The Phase 1 fixture `samples/sample.log` has 9 parsed events, 4 successes,
5 failures, 3 unique IPs, 5 unique usernames, 2 ignored blank lines, and
4 skipped nonblank lines. The independent line-by-line expectations are in
`samples/README.md`; the verified console output is in the root README.

## Detection rules — Phase 2

Evaluate events in UTC timestamp order, using original line number to break ties. Window endpoints are inclusive. Interleaved unrelated events must not reset a window. Findings describe suspicious activity, not confirmed attacks.

| Rule ID | Grouping | Default trigger |
| --- | --- | --- |
| repeated_failures | IP | At least 5 failures within 300 seconds |
| success_after_failures | IP and username | A success following at least 5 failures against that same account within the preceding 600 seconds |
| multiple_accounts | IP | Failures against at least 5 distinct usernames within 600 seconds |

Success-after-failures is independently evaluated against same-account failures; an IP-wide repeated-failures finding alone is insufficient. Only events preceding the success in the sorted event order contribute.

### Finding emission

For repeated failures and multiple accounts, emit on the first qualifying failure in an active episode. Suppress later findings for the same rule and group while the rolling window remains above threshold; start a new episode if it falls below threshold and later qualifies again. Keep the evidence window at the trigger rather than expanding it indefinitely.

For success after failures, emit one finding per qualifying successful event. Do not merge distinct successful events. Different rules may cite the same event.

Each finding contains a deterministic ID, rule ID, IP, affected usernames, trigger timestamp, evidence start/end timestamps, event count, applicable thresholds, a plain-language explanation, and supporting event records with line numbers. Use neutral wording, not an unsupported certainty or severity score.

## Configuration — Phase 3

Optional JSON configuration uses these integer fields:

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

Omitted fields use defaults. Require positive integers; reject booleans, unknown fields, invalid JSON, and non-object configuration with clear errors. Record effective configuration in exported reports.

## CLI and report contract

Phase 1: `python loginwatch.py PATH` displays the summary. Phase 2 adds findings. Phase 3 introduces `--config PATH` and `--json PATH`.

Exit 0 for completed analysis, including skipped lines or suspicious findings. Use nonzero status for input/configuration/output errors; show concise user-facing errors without routine tracebacks. Include argparse help.

Phase 1 implements argparse help now. Completed summaries exit 0; input read
or decoding errors exit 1 and write a concise message to stderr without a
traceback or partial summary. Argument errors exit 2. UTF-8 decoding is strict.

Planned Phase 3 JSON report contains schema_version, source filename, summary,
effective configuration, and findings. Serialize UTC timestamps consistently
with Z, order findings by trigger time then rule/group, and avoid generated
timestamps that prevent reproducible fixture comparisons. Console output can
abbreviate evidence; JSON preserves full supporting records. Exported reports
can contain sensitive log data; document this behavior in the README when
export is implemented.

## Quality and delivery

Cover normal activity, below-threshold behavior, exact thresholds, window boundaries, unrelated intervening events, out-of-order input, equivalent timezone offsets, malformed lines, IPv6, empty inputs, and CLI failures. Use only synthetic sample data and documentation IP ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32).

Keep the repository small and understandable. Document supported behavior and limitations rather than claiming general SSH compatibility or production readiness.
