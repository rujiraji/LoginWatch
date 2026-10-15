"""Immutable data passed between parsing, detection, and reporting."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class LoginEvent:
    timestamp: datetime
    ip: str
    username: str
    result: Literal["success", "failure"]
    line_number: int
    raw_line: str


@dataclass(frozen=True, slots=True)
class ParseResult:
    events: tuple[LoginEvent, ...]
    ignored_blank_lines: int
    skipped_lines: int


@dataclass(frozen=True, slots=True)
class ActivitySummary:
    parsed_events: int
    successful_logins: int
    failed_logins: int
    unique_ips: int
    unique_usernames: int
    ignored_blank_lines: int
    skipped_lines: int


RuleID = Literal["repeated_failures", "success_after_failures", "multiple_accounts"]


@dataclass(frozen=True, slots=True)
class Finding:
    id: str
    rule_id: RuleID
    ip: str
    usernames: tuple[str, ...]
    trigger_timestamp: datetime
    evidence_start: datetime
    evidence_end: datetime
    event_count: int
    threshold_count: int
    window_seconds: int
    explanation: str
    evidence: tuple[LoginEvent, ...]
