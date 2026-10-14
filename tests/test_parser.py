from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from parser import parse_file, parse_line, parse_lines


ROOT = Path(__file__).resolve().parents[1]


def log_line(
    message="Failed password for alice",
    timestamp="2026-10-11T10:00:00-05:00",
    ip="192.0.2.10",
    port="54321",
):
    return f"{timestamp} server sshd[1234]: {message} from {ip} port {port} ssh2"


class ParserTests(unittest.TestCase):
    def test_documented_message_forms(self):
        cases = (
            ("Failed password for alice", "alice", "failure"),
            ("Failed password for invalid user admin", "admin", "failure"),
            ("Accepted password for alice", "alice", "success"),
        )
        for message, username, result in cases:
            with self.subTest(message=message):
                raw = log_line(message=message)
                event = parse_line(raw, 7)
                self.assertIsNotNone(event)
                self.assertEqual(event.username, username)
                self.assertEqual(event.result, result)
                self.assertEqual(event.timestamp, datetime(2026, 10, 11, 15, tzinfo=timezone.utc))
                self.assertIs(event.timestamp.tzinfo, timezone.utc)
                self.assertEqual(event.ip, "192.0.2.10")
                self.assertEqual(event.line_number, 7)
                self.assertEqual(event.raw_line, raw)

    def test_equivalent_offsets_and_fractional_seconds(self):
        timestamps = (
            "2026-10-11T10:00:00.123456-05:00",
            "2026-10-11T15:00:00.123456Z",
            "2026-10-11T17:00:00.123456+02:00",
            "2026-10-11T17:00:00.123456+0200",
            "2026-10-11T15:00:00.123456789Z",
        )
        for timestamp in timestamps:
            with self.subTest(timestamp=timestamp):
                event = parse_line(log_line(timestamp=timestamp), 1)
                self.assertIsNotNone(event)
                self.assertEqual(
                    event.timestamp,
                    datetime(2026, 10, 11, 15, microsecond=123456, tzinfo=timezone.utc),
                )

    def test_ipv6_normalization(self):
        event = parse_line(log_line(ip="2001:0DB8:0000:0000:0000:0000:0000:0001"), 1)
        self.assertIsNotNone(event)
        self.assertEqual(event.ip, "2001:db8::1")

    def test_port_boundaries(self):
        for port in ("1", "65535", "00001"):
            with self.subTest(port=port):
                self.assertIsNotNone(parse_line(log_line(port=port), 1))

    def test_invalid_timestamps_are_skipped(self):
        timestamps = (
            "2026-10-11T10:00:00",  # timezone missing
            "Oct-11T10:00:00Z",  # traditional syslog is unsupported
            "2026-02-30T10:00:00Z",
            "2026-10-11T24:00:00Z",
            "2026-10-11T10:60:00Z",
            "2026-10-11T10:00:60Z",
            "2026-10-11T10:00:00+24:00",
            "2026-10-11T10:00:00+00:60",
            "2026-10-11T10:00:00z",
            "0001-01-01T00:00:00+01:00",  # UTC would underflow datetime
        )
        for timestamp in timestamps:
            with self.subTest(timestamp=timestamp):
                self.assertIsNone(parse_line(log_line(timestamp=timestamp), 1))

    def test_invalid_addresses_and_ports_are_skipped(self):
        for ip in ("203.0.113.999", "hostname", "2001:db8:::1", "2001:db8::1%local"):
            with self.subTest(ip=ip):
                self.assertIsNone(parse_line(log_line(ip=ip), 1))
        for port in ("0", "65536", "-1", "1.0", "abc", "9" * 5000):
            with self.subTest(port=port[:20]):
                self.assertIsNone(parse_line(log_line(port=port), 1))

    def test_unsupported_or_incomplete_structure_is_skipped(self):
        raw = log_line()
        lines = (
            log_line(message="Accepted publickey for alice"),
            log_line(message="Accepted password for invalid user admin"),
            log_line(message="Failed password for first last"),
            log_line(message="Failed password for"),
            raw.replace("sshd[1234]", "ssh[1234]"),
            raw.replace("sshd[1234]", "sshd[pid]"),
            raw.replace("server sshd", "sshd"),
            raw.replace(" from ", " via "),
            raw.replace(" port ", " socket "),
            raw.removesuffix(" ssh2"),
            raw + " extra text",
            "unrelated log entry",
        )
        for line in lines:
            with self.subTest(line=line):
                self.assertIsNone(parse_line(line, 1))

    def test_evidence_preserves_spacing_and_excludes_line_ending(self):
        raw = "  " + log_line() + "  "
        event = parse_line(raw + "\r\n", 4)
        self.assertIsNotNone(event)
        self.assertEqual(event.raw_line, raw)

    def test_blanks_skips_duplicates_and_source_order(self):
        later = log_line(timestamp="2026-10-11T16:00:00Z")
        earlier = log_line(timestamp="2026-10-11T15:00:00Z")
        parsed = parse_lines([later, "\n", " \t\r\n", "unsupported", earlier, later])
        self.assertEqual(parsed.ignored_blank_lines, 2)
        self.assertEqual(parsed.skipped_lines, 1)
        self.assertEqual([event.line_number for event in parsed.events], [1, 5, 6])
        self.assertGreater(parsed.events[0].timestamp, parsed.events[1].timestamp)
        self.assertEqual(parsed.events[0].raw_line, parsed.events[2].raw_line)

    def test_empty_and_no_supported_events(self):
        parsed = parse_lines([])
        self.assertEqual(parsed.events, ())
        self.assertEqual(parsed.ignored_blank_lines, 0)
        self.assertEqual(parsed.skipped_lines, 0)
        parsed = parse_lines(["\n", "unsupported", "another unsupported line"])
        self.assertEqual(parsed.events, ())
        self.assertEqual(parsed.ignored_blank_lines, 1)
        self.assertEqual(parsed.skipped_lines, 2)

    def test_utf8_username_and_file_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.log"
            original = (log_line(message="Accepted password for josé") + "\r\n").encode("utf-8")
            path.write_bytes(original)
            parsed = parse_file(path)
            self.assertEqual(parsed.events[0].username, "josé")
            self.assertEqual(path.read_bytes(), original)

    def test_missing_and_invalid_utf8_files_raise(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.log"
            with self.assertRaises(FileNotFoundError):
                parse_file(path)
            original = (log_line() + "\n").encode("utf-8") + b"\xff"
            path.write_bytes(original)
            with self.assertRaises(UnicodeDecodeError):
                parse_file(path)
            self.assertEqual(path.read_bytes(), original)

    def test_sample_evidence_matches_documented_lines(self):
        parsed = parse_file(ROOT / "samples" / "sample.log")
        self.assertEqual([event.line_number for event in parsed.events], list(range(1, 10)))
        self.assertEqual(parsed.events[1].username, "admin")
        self.assertEqual(parsed.events[2].timestamp, parsed.events[7].timestamp)
        self.assertEqual(parsed.events[5].ip, parsed.events[6].ip)
        self.assertEqual(parsed.events[0].raw_line, parsed.events[8].raw_line)
