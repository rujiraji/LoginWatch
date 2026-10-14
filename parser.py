"""Parse the documented SSH password-login format without changing input files."""

from datetime import datetime, timezone
from ipaddress import ip_address
from pathlib import Path
import re
from typing import Iterable

from models import LoginEvent, ParseResult


_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]+)?(?:Z|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])"
)
_MESSAGE = re.compile(
    r"(?P<timestamp>\S+)\s+\S+\s+sshd\[[0-9]+\]:\s+"
    r"(?:(?P<failure>Failed) password for (?:invalid user )?|Accepted password for )"
    r"(?P<username>\S+) from (?P<ip>\S+) port (?P<port>[0-9]+) ssh2"
)


def parse_line(raw_line: str, line_number: int) -> LoginEvent | None:
    """Return an event, or None for an unsupported or malformed line."""
    raw_line = raw_line.rstrip("\r\n")
    match = _MESSAGE.fullmatch(raw_line.strip())
    if match is None or _TIMESTAMP.fullmatch(match["timestamp"]) is None:
        return None
    try:
        timestamp = datetime.fromisoformat(match["timestamp"]).astimezone(timezone.utc)
        # Zone identifiers name local interfaces, rather than plain IP addresses.
        if "%" in match["ip"]:
            return None
        ip = str(ip_address(match["ip"]))
        port = int(match["port"])
    except (ValueError, OverflowError):
        return None
    if not 1 <= port <= 65535:
        return None
    return LoginEvent(
        timestamp=timestamp,
        ip=ip,
        username=match["username"],
        result="failure" if match["failure"] else "success",
        line_number=line_number,
        raw_line=raw_line,
    )


def parse_lines(lines: Iterable[str]) -> ParseResult:
    """Retain input order and distinguish blank lines from skipped records."""
    events = []
    ignored_blank_lines = 0
    skipped_lines = 0
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            ignored_blank_lines += 1
            continue
        event = parse_line(raw_line, line_number)
        if event is None:
            skipped_lines += 1
        else:
            events.append(event)
    return ParseResult(tuple(events), ignored_blank_lines, skipped_lines)


def parse_file(path: str | Path) -> ParseResult:
    """Read strict UTF-8; let the CLI handle file and decoding errors."""
    with open(path, encoding="utf-8") as source:
        return parse_lines(source)
