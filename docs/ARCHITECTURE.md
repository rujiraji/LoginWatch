# Architecture and interview notes

The CLI coordinates a pipeline: configuration and log input → validated
events → ordered detection → findings → console/JSON formatting → optional
atomic export. The summary uses all successfully parsed events, independently
of whether any rule triggers. Runtime modules use Python's standard library.

| Component | Input | Output and responsibility |
| --- | --- | --- |
| `loginwatch.py` | Paths and CLI options | Coordinates the pipeline, handles user-facing errors, returns status; exports before printing console output |
| `configuration.py` | Optional UTF-8 JSON | Validated frozen `DetectionConfig`; omitted fields use defaults; rejects duplicate/unknown keys and invalid integer types/ranges |
| `parser.py` | UTF-8 source lines | `ParseResult` with immutable events, blank/skipped counts, original text and line numbers; normalizes timestamps to UTC and IP spelling |
| `models.py` | Structured values | Immutable events, parser results, summaries, and findings passed between components |
| `analyzer.py` | Events and effective configuration | Sorted view by UTC timestamp/source line; independent rules return ordered evidence snapshots without mutating input |
| `reporter.py` | Parsed counts, configuration, findings | Summary, console explanations, and deterministic schema 1.0 JSON with every supporting event |
| `report_export.py` | JSON text, destination, protected source paths | Checks aliases and writes through a temporary file in the destination directory before atomic replacement |

`scripts/verify_demo.py` is a delivery check, outside the runtime pipeline.
It drives CLI subprocesses using synthetic fixtures and independent constants.
CI runs the existing unittest suite; it adds no runtime dependencies.

## Decisions to explain

**Inclusive windows.** A failure at exactly `trigger_time - window` is retained.
The analyzer removes records only when their age exceeds the configured
window. It compares time differences rather than subtracting a cutoff from
the minimum supported datetime. Positive 32-bit configuration bounds keep
`timedelta` construction safe. Tests cover boundaries and one microsecond beyond.

**Correlation and ordering.** Repeated failures and multiple accounts group by
IP. Success after failures groups by IP and case-sensitive username, using
only failures earlier in `(timestamp, source line)` order. Equal-time failures
after the successful source line cannot contribute. Unrelated interleaved
events do not reset histories. Each qualifying success gets a separate finding.

**Episodes.** Failure rules suppress later findings while their rolling evidence
remains at or above threshold. At the next relevant failure, old evidence
expires first. If the remaining count drops below threshold, the rule rearms
before the new failure is appended. This detects a new episode even when the
drop happened during a silent gap and the next event immediately restores
the threshold. Evidence is frozen at emission; it does not grow afterward.

**Determinism.** Explicit event/finding order, UTC timestamps, sorted usernames
and JSON keys, fixed formatting, and no generated time make equivalent runs
produce identical bytes. IDs combine rule, normalized IP, and triggering line.
They are scoped to a source, not globally unique; moving lines can change IDs.
Raw text is preserved, so changing its spelling can also change report bytes.

**Atomic export.** Resolved paths and filesystem identity checks protect the
input/configuration from direct, symbolic-link, and hard-link collisions. A
second check runs before replacement. A temporary file in the destination
directory is written, flushed, fsynced, and closed before `os.replace`.
Failures preserve the old report and clean up the temporary file. Replacing an
unrelated destination symlink replaces the link entry, not its target. This
does not coordinate concurrent filesystem changes or guarantee directory-entry
crash durability.

## Interview prompts

- Trace one failed login from source line to a finding's JSON evidence record.
- Explain why an IP-wide repeated-failure finding alone cannot justify a success-after-failures finding.
- Use suspicious lines 13–14 to explain expiration, suppression, and rearming.
- Explain why a success finding has one more evidence record than its failure threshold.
- Describe what must stay the same for byte-identical reports and what edits change IDs.
- Explain how a failed export preserves an existing report and what atomic replacement cannot guarantee.
- State the tradeoff of holding events/evidence in memory and why no large-log performance claim is supported.

These are discussion prompts, not assertions about the owner's interview
performance. [PORTFOLIO.md](PORTFOLIO.md) records the actual contribution split.
