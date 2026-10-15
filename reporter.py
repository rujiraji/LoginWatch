"""Format activity counts and evidence-backed findings for the console."""

from datetime import datetime
from typing import Iterable

from models import ActivitySummary, Finding, ParseResult


def summarize(parsed: ParseResult) -> ActivitySummary:
    successes = sum(event.result == "success" for event in parsed.events)
    return ActivitySummary(
        parsed_events=len(parsed.events),
        successful_logins=successes,
        failed_logins=len(parsed.events) - successes,
        unique_ips=len({event.ip for event in parsed.events}),
        unique_usernames=len({event.username for event in parsed.events}),
        ignored_blank_lines=parsed.ignored_blank_lines,
        skipped_lines=parsed.skipped_lines,
    )


def format_summary(summary: ActivitySummary) -> str:
    return "\n".join(
        (
            "LoginWatch activity summary",
            f"Parsed events: {summary.parsed_events}",
            f"Successful logins: {summary.successful_logins}",
            f"Failed logins: {summary.failed_logins}",
            f"Unique IPs: {summary.unique_ips}",
            f"Unique usernames: {summary.unique_usernames}",
            f"Ignored blank lines: {summary.ignored_blank_lines}",
            f"Skipped nonblank lines: {summary.skipped_lines}",
        )
    )


def _utc_text(timestamp: datetime) -> str:
    return timestamp.isoformat().replace("+00:00", "Z")


def format_findings(findings: Iterable[Finding]) -> str:
    findings = tuple(findings)
    lines = [f"Findings: {len(findings)}"]
    if not findings:
        lines.append("No suspicious patterns detected by the three default rules.")
    for finding in findings:
        lines.extend((
            "",
            f"[{finding.id}] {finding.rule_id}",
            f"Trigger: {_utc_text(finding.trigger_timestamp)}",
            f"IP: {finding.ip}; usernames: {', '.join(finding.usernames)}",
            finding.explanation,
            f"Evidence: {finding.event_count} events, "
            f"{_utc_text(finding.evidence_start)} to {_utc_text(finding.evidence_end)}",
            "Supporting source lines:",
        ))
        lines.extend(
            f"  line {event.line_number}: {event.raw_line}" for event in finding.evidence
        )
    return "\n".join(lines)
