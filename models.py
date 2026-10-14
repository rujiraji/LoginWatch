"""Data passed between the parser and activity reporter."""

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
