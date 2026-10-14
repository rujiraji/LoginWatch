"""Deterministic Phase 2 rules over a sorted view of parsed events."""

from collections import deque
from datetime import datetime, timedelta
from typing import Iterable

from models import Finding, LoginEvent, RuleID


THRESHOLD_COUNT = 5


def _expire(queue: deque[LoginEvent], now: datetime, window_seconds: int) -> None:
    """Keep both window endpoints inclusive, including fractional seconds."""
    window = timedelta(seconds=window_seconds)
    while queue and now - queue[0].timestamp > window:
        queue.popleft()


def _finding(
    rule_id: RuleID,
    trigger: LoginEvent,
    evidence: tuple[LoginEvent, ...],
    window_seconds: int,
    explanation: str,
) -> Finding:
    return Finding(
        id=f"{rule_id}:{trigger.ip}:line-{trigger.line_number}",
        rule_id=rule_id,
        ip=trigger.ip,
        usernames=tuple(sorted({event.username for event in evidence})),
        trigger_timestamp=trigger.timestamp,
        evidence_start=evidence[0].timestamp,
        evidence_end=evidence[-1].timestamp,
        event_count=len(evidence),
        threshold_count=THRESHOLD_COUNT,
        window_seconds=window_seconds,
        explanation=explanation,
        evidence=evidence,
    )


def _failure_findings(
    events: list[LoginEvent], rule_id: RuleID, window_seconds: int
) -> list[Finding]:
    """Emit once per IP episode, rearming after expiry before adding a failure."""
    queues: dict[str, deque[LoginEvent]] = {}
    active: set[str] = set()
    findings = []

    def count(queue: deque[LoginEvent]) -> int:
        if rule_id == "multiple_accounts":
            return len({event.username for event in queue})
        return len(queue)

    for event in events:
        if event.result != "failure":
            continue
        queue = queues.setdefault(event.ip, deque())
        _expire(queue, event.timestamp, window_seconds)
        # Expiry can end an episode during a gap, even if this failure will
        # immediately restore the threshold. Check before appending it.
        if count(queue) < THRESHOLD_COUNT:
            active.discard(event.ip)
        queue.append(event)
        if count(queue) < THRESHOLD_COUNT or event.ip in active:
            continue
        active.add(event.ip)
        if rule_id == "multiple_accounts":
            explanation = (
                f"{len(queue)} failed password logins from {event.ip} involved "
                f"{count(queue)} distinct usernames within {window_seconds} seconds "
                f"(threshold: {THRESHOLD_COUNT} distinct usernames)."
            )
        else:
            explanation = (
                f"{len(queue)} failed password logins from {event.ip} occurred "
                f"within {window_seconds} seconds (threshold: {THRESHOLD_COUNT} failures)."
            )
        findings.append(_finding(rule_id, event, tuple(queue), window_seconds, explanation))
    return findings


def _success_findings(events: list[LoginEvent]) -> list[Finding]:
    queues: dict[tuple[str, str], deque[LoginEvent]] = {}
    findings = []
    window_seconds = 600
    for event in events:
        key = (event.ip, event.username)
        queue = queues.setdefault(key, deque())
        _expire(queue, event.timestamp, window_seconds)
        if event.result == "failure":
            queue.append(event)
        elif len(queue) >= THRESHOLD_COUNT:
            explanation = (
                f"A successful password login for '{event.username}' from {event.ip} "
                f"followed {len(queue)} failures against the same IP and username "
                f"within the preceding {window_seconds} seconds "
                f"(threshold: {THRESHOLD_COUNT} failures)."
            )
            evidence = (*queue, event)
            findings.append(_finding(
                "success_after_failures", event, evidence, window_seconds, explanation
            ))
    return findings


def analyze(events: Iterable[LoginEvent]) -> tuple[Finding, ...]:
    """Analyze without changing events or source order; use the fixed defaults."""
    ordered = sorted(events, key=lambda event: (event.timestamp, event.line_number))
    findings = (
        _failure_findings(ordered, "repeated_failures", 300)
        + _success_findings(ordered)
        + _failure_findings(ordered, "multiple_accounts", 600)
    )
    return tuple(sorted(findings, key=lambda finding: (
        finding.trigger_timestamp,
        finding.rule_id,
        finding.ip,
        finding.usernames,
        finding.evidence[-1].line_number,
    )))
