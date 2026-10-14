"""Summarize parsed events and format their activity counts for the console."""

from models import ActivitySummary, ParseResult


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
