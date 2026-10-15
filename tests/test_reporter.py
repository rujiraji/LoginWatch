from dataclasses import asdict
from pathlib import Path
import unittest

from models import ActivitySummary
from analyzer import analyze
from parser import parse_file, parse_lines
from reporter import format_findings, format_summary, summarize


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SAMPLE_OUTPUT = """LoginWatch activity summary
Parsed events: 9
Successful logins: 4
Failed logins: 5
Unique IPs: 3
Unique usernames: 5
Ignored blank lines: 2
Skipped nonblank lines: 4"""


class ReporterTests(unittest.TestCase):
    def test_sample_totals_match_independently_documented_expectations(self):
        summary = summarize(parse_file(ROOT / "samples" / "sample.log"))
        # These constants come from the line-by-line expectations in samples/README.md.
        self.assertEqual(asdict(summary), {
            "parsed_events": 9,
            "successful_logins": 4,
            "failed_logins": 5,
            "unique_ips": 3,
            "unique_usernames": 5,
            "ignored_blank_lines": 2,
            "skipped_lines": 4,
        })
        self.assertEqual(summary.parsed_events, summary.successful_logins + summary.failed_logins)
        self.assertEqual(format_summary(summary), EXPECTED_SAMPLE_OUTPUT)

    def test_empty_summary(self):
        self.assertEqual(summarize(parse_lines([])), ActivitySummary(0, 0, 0, 0, 0, 0, 0))

    def test_no_supported_events_summary(self):
        parsed = parse_lines(["unsupported\n", "\n", "more unsupported\n"])
        self.assertEqual(summarize(parsed), ActivitySummary(0, 0, 0, 0, 0, 1, 2))

    def test_case_sensitive_usernames_and_normalized_ips(self):
        prefix = "2026-10-11T15:00:00Z server sshd[1]: "
        parsed = parse_lines([
            prefix + "Accepted password for alice from 2001:0db8::1 port 1 ssh2",
            prefix + "Failed password for Alice from 2001:db8::1 port 65535 ssh2",
            prefix + "Failed password for ignored from 203.0.113.10 port 0 ssh2",
        ])
        self.assertEqual(summarize(parsed), ActivitySummary(2, 1, 1, 1, 2, 0, 1))

    def test_no_findings_console_text(self):
        self.assertEqual(format_findings([]), "Findings: 0\n"
                         "No suspicious patterns detected by the three rules.")

    def test_findings_console_includes_utc_metadata_reason_and_raw_evidence(self):
        parsed = parse_file(ROOT / "samples" / "suspicious.log")
        finding = analyze(parsed.events)[0]
        rendered = format_findings([finding])
        self.assertIn("Findings: 1\n", rendered)
        self.assertIn("Trigger: 2026-10-11T10:05:00Z", rendered)
        self.assertIn("IP: 192.0.2.10; usernames: alice", rendered)
        self.assertIn("5 failed password logins from 192.0.2.10 occurred within 300 seconds", rendered)
        self.assertIn("Evidence: 5 events, 2026-10-11T10:00:00Z to 2026-10-11T10:05:00Z", rendered)
        for record in parsed.events[:5]:
            self.assertIn(f"  line {record.line_number}: {record.raw_line}", rendered)
        self.assertNotIn("  line 6:", rendered)
