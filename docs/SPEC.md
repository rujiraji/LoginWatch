# LoginWatch specification

Status: design baseline, version 0.1. Phase 1 input, events, activity summary,
and positional-path CLI are Accepted following owner-reported independent
review of commit `aaa183c0adfe37a734a5431bf8b1db51b930ce22`. Detection and console
evidence (Phase 2) are Accepted following owner-reported independent review of
commit `4b51f8e998a6dfe193d2a95000859ee382c83342` in PR #2. Configuration/JSON export
(Phase 3) are Implemented — awaiting review.

## Goal and user workflow

A user supplies a local SSH log file. LoginWatch parses supported events, summarizes activity, identifies configured suspicious patterns, and reports the evidence behind each finding. Successful delivery means another person can reproduce the sample results using the README.

## First-release scope

Planned first release: Python CLI, one documented password-login format, IPv4
and IPv6, three detection rules, configurable thresholds, console output, JSON
export, synthetic fixtures, meaningful tests, and a repeatable demo. Phase 1
delivers parsing and console summary; Phase 2 adds default detection rules and
console evidence. Phase 3 adds validated effective configuration and JSON
export; Phase 4 release/portfolio delivery remains planned.

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

Analyze a sorted view; never mutate parsed events or their source ordering.
Phase 2 introduced the defaults below. Phase 3 passes immutable validated
effective configuration into the analyzer; omitted configuration uses these
same defaults and preserves the established semantics.

| Rule ID | Grouping | Default trigger |
| --- | --- | --- |
| repeated_failures | IP | At least 5 failures within 300 seconds |
| success_after_failures | IP and username | A success following at least 5 failures against that same account within the preceding 600 seconds |
| multiple_accounts | IP | Failures against at least 5 distinct usernames within 600 seconds |

Success-after-failures is independently evaluated against same-account failures; an IP-wide repeated-failures finding alone is insufficient. Only events preceding the success in the sorted event order contribute.

### Finding emission

For repeated failures and multiple accounts, emit on the first qualifying failure in an active episode. Suppress later findings for the same rule and group while the rolling window remains at or above threshold; start a new episode if it falls below threshold and later qualifies again. Keep the evidence window at the trigger rather than expanding it indefinitely.

An episode ends when expiration reduces qualifying evidence below threshold,
including during a gap with no events. Before adding each new failure, expire
old evidence and check the remaining count (failures or distinct usernames).
If it is below threshold, rearm the rule for that IP; then add the new failure
and evaluate. That failure can immediately restore the threshold and emit a
new finding. Evidence exactly `window_seconds` before the event remains
included; only older evidence expires. Expiring some evidence while the
remaining evidence is still at or above threshold does not end the episode.
Successes do not reset failure episodes or clear failure history. Episode
state is independent per rule and IP. Expiration is evaluated lazily at the
next relevant event, yielding the same findings as expiry during silent gaps.

For success after failures, emit one finding per qualifying successful event. Do not merge distinct successful events. Different rules may cite the same event.

Each finding contains a deterministic ID, rule ID, IP, affected usernames, trigger timestamp, evidence start/end timestamps, event count, applicable thresholds, a plain-language explanation, and supporting event records with line numbers. Use neutral wording, not an unsupported certainty or severity score.

Implemented `Finding` fields: `id`, `rule_id`, `ip`, sorted unique `usernames`,
`trigger_timestamp`, `evidence_start`, `evidence_end`, `event_count`,
`threshold_count`, `window_seconds`, `explanation`, and immutable `evidence`.
`threshold_count` measures failures for the first two rules and distinct
usernames for `multiple_accounts`.

Evidence membership:

- Repeated failures: all IP-matching failures in the inclusive configured window (default 300 seconds), including the triggering failure.
- Multiple accounts: all IP-matching failures in the inclusive configured window (default 600 seconds), including repeated usernames and the trigger, rather than one representative per account.
- Success after failures: all preceding same-IP/account failures in the inclusive configured window (default 600 seconds), followed by the triggering success. Other successes and failures after that success in sorted order are excluded.

`event_count` is the number of supporting records, including the success for
success-after-failures. Evidence records retain timestamp/source-line ordering.
Start/end times are the first/last evidence timestamps. Snapshots never grow
after emission. IDs use `<rule_id>:<normalized IP>:line-<trigger source line>`;
they are scoped to the analyzed source and stable across identical runs.
They are not globally unique across files, and line-number changes change IDs.
Findings sort by trigger timestamp, rule ID, IP, usernames, and triggering
source line as a final tie-breaker.

`samples/normal.log` independently expects no findings; `samples/suspicious.log`
expects one repeated-failure finding, two qualifying-success findings, and two
multiple-account episodes. Exact trigger/evidence lines and explanations of
these expectations are in `samples/README.md`.

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

Phase 3 implementation contract (defined before implementation; verification
and platform limitations are recorded in PLAN):

- `--config PATH` reads strict UTF-8 JSON without modifying it. An omitted configuration or `{}` uses all defaults; a partial object overrides only named fields.
- All six values must have integer type (not booleans), in `1..2147483647` inclusive. This common positive 32-bit bound keeps windows safely representable by Python `timedelta` and makes the contract portable; counts use the same bound. Larger integers are rejected before analysis, not used in timestamp arithmetic.
- Reject floats, strings, nulls, arrays, non-object roots, duplicate keys (including nested objects), unknown keys, malformed JSON, and non-finite JSON constants. Read/decoding/validation failures return concise errors without routine tracebacks. Excessively nested JSON is rejected clearly as well.
- Pass a frozen effective configuration to the analyzer. The default values preserve Phase 2 ordering, evidence, IDs, and episode semantics. Every finding records and explains its actual count/window thresholds. Console wording refers to the three rules, including when configured values differ from defaults.

### JSON schema version 1.0

`--json PATH` retains console reporting and writes this exact structure. No
generated time, absolute source path, host details, or other environment
metadata is added. No fields are optional in schema 1.0.

| Object | Fields and JSON types |
| --- | --- |
| Root | `schema_version`: string `"1.0"`; `source_filename`: source log basename string; `summary`: object; `effective_configuration`: object; `findings`: array |
| Summary | `parsed_events`, `successful_logins`, `failed_logins`, `unique_ips`, `unique_usernames`, `ignored_blank_lines`, `skipped_lines`: nonnegative integers |
| Effective configuration | All six fields from the configuration object above, with effective integer values including defaults |
| Finding | `id`, `rule_id`, `ip`: strings; `usernames`: sorted unique string array; `trigger_timestamp`, `evidence_start`, `evidence_end`: UTC timestamp strings; `event_count`, `threshold_count`, `window_seconds`: positive integers; `explanation`: string; `evidence`: array of event objects |
| Supporting event | `timestamp`: UTC timestamp string; `ip`, `username`: strings; `result`: `"success"` or `"failure"`; `line_number`: positive integer; `raw_line`: original event text string excluding its line ending |

Timestamp metadata uses `YYYY-MM-DDTHH:MM:SSZ`, or six fractional digits
before `Z` when microseconds are nonzero. Original timestamp spellings remain
in `raw_line`. Findings use the established trigger/rule/group/source-line
order; evidence keeps timestamp/source-line order. Empty/no-finding reports
use `findings: []` and the normal summary counts.

JSON bytes are UTF-8 without BOM, with literal Unicode, recursively sorted
object keys, two-space indentation, LF newlines, and exactly one trailing LF.
Equivalent input records, source basename, and effective configuration produce
identical bytes. Destination path and working-directory spelling do not affect
the report. Every finding field and every supporting record is preserved;
reports retain usernames and raw log text and may contain sensitive data.

### Atomic export and path protection

The destination directory must already exist. On success, an existing report
entry is replaced. Write a temporary file in that directory, flush and fsync
it, close it, then atomically replace the destination. Clean up the temporary
file on failures; preserve an existing report until successful replacement.
This is atomic file replacement, not a guarantee of crash durability for the
directory entry or coordination with concurrent filesystem changes.

Reject a destination referring to the input log or configuration, using
resolved-path comparisons and filesystem identity checks for existing files.
This includes relative paths, symbolic links, parent-directory links, and hard
links where supported. Check before writing and again before replacement.
For an allowed destination symlink to an unrelated report, replace the symlink
entry itself, leaving its old target untouched. Input and configuration files
are never written. Invalid paths and write/replace failures produce clear
errors and nonzero status; no console report is printed on configuration or
JSON export failure.

## CLI and report contract

Phase 1: `python loginwatch.py PATH` displays the summary. Phase 2 adds findings. Phase 3 introduces `--config PATH` and `--json PATH`.

Exit 0 for completed analysis, including skipped lines or suspicious findings. Use nonzero status for input/configuration/output errors; show concise user-facing errors without routine tracebacks. Include argparse help.

Phase 1 implements argparse help now. Completed summaries exit 0; input read
or decoding errors exit 1 and write a concise message to stderr without a
traceback or partial summary. Argument errors exit 2. UTF-8 decoding is strict.

Phase 2 preserves these summary and error behaviors and appends a findings
section after a blank line. The section always reports `Findings: N`. Zero
findings in Phase 3 are followed by `No suspicious patterns detected by the
three rules.` This updates Phase 2's reference to defaults, since rules can
now be configured. Each finding prints its ID/rule, UTC trigger, IP/usernames, reason and
threshold, evidence count/time range, and all original supporting records
prefixed by source line number. UTC metadata uses ISO timestamps ending in
`Z`; raw evidence retains its original timestamp spelling. All input is read
successfully before any summary or findings are printed. Findings still exit 0.

Phase 3 implements `--config` and `--json` under the contracts above.
Configuration, input, and export failures exit 1 with concise stderr errors
and no routine traceback. CLI argument errors still exit 2. All JSON export
work completes before console reporting; successful findings still exit 0.
The console and JSON both preserve complete supporting records. Exported
reports retain usernames and raw source text; the README documents that
sensitivity and the replacement policy.

## Quality and delivery

Cover normal activity, below-threshold behavior, exact thresholds, window boundaries, unrelated intervening events, out-of-order input, equivalent timezone offsets, malformed lines, IPv6, empty inputs, and CLI failures. Use only synthetic sample data and documentation IP ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32).

Keep the repository small and understandable. Document supported behavior and limitations rather than claiming general SSH compatibility or production readiness.
