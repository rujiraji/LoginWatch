from dataclasses import asdict
import json
from pathlib import Path
import unittest

from analyzer import analyze
from configuration import DetectionConfig, load_config
from parser import parse_file, parse_lines
from reporter import format_json_report, summarize
from test_analyzer import event
from test_configuration import DEFAULTS


ROOT = Path(__file__).resolve().parents[1]


class JsonReportTests(unittest.TestCase):
    def fixture_report(self, name="suspicious.log", config=None):
        path = ROOT / "samples" / name
        parsed = parse_file(path)
        config = config or DetectionConfig()
        return format_json_report(path, summarize(parsed), config, analyze(parsed.events, config))

    def test_exact_root_schema_and_effective_defaults(self):
        report = json.loads(self.fixture_report())
        self.assertEqual(set(report), {"schema_version", "source_filename", "summary", "effective_configuration", "findings"})
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["source_filename"], "suspicious.log")
        self.assertEqual(report["effective_configuration"], DEFAULTS)
        self.assertEqual(report["summary"], {
            "parsed_events": 14, "successful_logins": 3, "failed_logins": 11,
            "unique_ips": 3, "unique_usernames": 7, "ignored_blank_lines": 0, "skipped_lines": 0,
        })

    def test_all_finding_fields_and_exact_first_finding(self):
        report = json.loads(self.fixture_report())
        first = report["findings"][0]
        self.assertEqual(set(first), {
            "id", "rule_id", "ip", "usernames", "trigger_timestamp", "evidence_start", "evidence_end",
            "event_count", "threshold_count", "window_seconds", "explanation", "evidence",
        })
        self.assertEqual({key: value for key, value in first.items() if key != "evidence"}, {
            "id": "repeated_failures:192.0.2.10:line-5", "rule_id": "repeated_failures",
            "ip": "192.0.2.10", "usernames": ["alice"], "trigger_timestamp": "2026-10-11T10:05:00Z",
            "evidence_start": "2026-10-11T10:00:00Z", "evidence_end": "2026-10-11T10:05:00Z",
            "event_count": 5, "threshold_count": 5, "window_seconds": 300,
            "explanation": "5 failed password logins from 192.0.2.10 occurred within 300 seconds (threshold: 5 failures).",
        })

    def test_exact_finding_order_and_all_evidence_membership(self):
        found = json.loads(self.fixture_report())["findings"]
        self.assertEqual([(f["rule_id"], [e["line_number"] for e in f["evidence"]]) for f in found], [
            ("repeated_failures", [1, 2, 3, 4, 5]),
            ("success_after_failures", [1, 2, 3, 4, 5, 6]),
            ("success_after_failures", [1, 2, 3, 4, 5, 7]),
            ("multiple_accounts", [9, 10, 11, 12, 13]),
            ("multiple_accounts", [10, 11, 12, 13, 14]),
        ])
        self.assertEqual([f["event_count"] for f in found], [5, 6, 6, 5, 5])
        self.assertEqual([f["trigger_timestamp"] for f in found], [
            "2026-10-11T10:05:00Z", "2026-10-11T10:05:01Z", "2026-10-11T10:05:02Z",
            "2026-10-11T10:30:00Z", "2026-10-11T10:30:01Z",
        ])

    def test_every_supporting_event_field_and_original_text(self):
        report = json.loads(self.fixture_report())
        raw_lines = (ROOT / "samples" / "suspicious.log").read_text(encoding="utf-8").splitlines()
        for finding in report["findings"]:
            for record in finding["evidence"]:
                self.assertEqual(set(record), {"timestamp", "ip", "username", "result", "line_number", "raw_line"})
                self.assertEqual(record["raw_line"], raw_lines[record["line_number"] - 1])
                self.assertTrue(record["timestamp"].endswith("Z"))
        self.assertEqual(report["findings"][1]["evidence"][-1]["result"], "success")
        self.assertEqual(report["findings"][0]["evidence"][0], {
            "timestamp": "2026-10-11T10:00:00Z", "ip": "192.0.2.10", "username": "alice",
            "result": "failure", "line_number": 1, "raw_line": raw_lines[0],
        })

    def test_utc_fractional_timestamps_and_literal_unicode_preserve_raw_spelling(self):
        record = event(0, 1, username="josé", timestamp="2026-10-11T05:00:00.123456-05:00")
        parsed = parse_lines([record.raw_line])
        config = DetectionConfig(repeated_failures_count=1)
        text = format_json_report("unicode.log", summarize(parsed), config, analyze(parsed.events, config))
        finding = json.loads(text)["findings"][0]
        for field in ("trigger_timestamp", "evidence_start", "evidence_end"):
            self.assertEqual(finding[field], "2026-10-11T10:00:00.123456Z")
        self.assertEqual(finding["evidence"][0]["timestamp"], "2026-10-11T10:00:00.123456Z")
        self.assertEqual(finding["evidence"][0]["raw_line"], record.raw_line)
        self.assertIn("josé", text)
        self.assertNotIn(r"jos\u00e9", text)

    def test_deterministic_sorted_keys_indentation_and_newline_format(self):
        first, second = self.fixture_report(), self.fixture_report()
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        self.assertTrue(first.endswith("\n"))
        self.assertFalse(first.endswith("\n\n"))
        self.assertNotIn("\r", first)
        self.assertTrue(first.startswith('{\n  "effective_configuration": {\n'))
        self.assertNotIn("generated", first)
        self.assertNotIn(str(ROOT), first)

    def test_source_basename_makes_equivalent_paths_identical(self):
        parsed = parse_file(ROOT / "samples" / "suspicious.log")
        args = (summarize(parsed), DetectionConfig(), analyze(parsed.events))
        self.assertEqual(format_json_report(ROOT / "samples" / "suspicious.log", *args),
                         format_json_report("samples/suspicious.log", *args))

    def test_empty_and_no_supported_event_reports(self):
        for lines, blanks, skipped in (([], 0, 0), (["\n", "unsupported"], 1, 1)):
            with self.subTest(lines=lines):
                parsed = parse_lines(lines)
                text = format_json_report("empty.log", summarize(parsed), DetectionConfig(), analyze(parsed.events))
                report = json.loads(text)
                self.assertEqual(report["findings"], [])
                self.assertEqual(report["summary"], {
                    "parsed_events": 0, "successful_logins": 0, "failed_logins": 0,
                    "unique_ips": 0, "unique_usernames": 0,
                    "ignored_blank_lines": blanks, "skipped_lines": skipped,
                })

    def test_normal_report_with_no_findings(self):
        report = json.loads(self.fixture_report("normal.log"))
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["summary"]["parsed_events"], 8)

    def test_custom_effective_config_and_actual_thresholds(self):
        config = load_config(ROOT / "samples" / "custom-config.json")
        report = json.loads(self.fixture_report("custom.log", config))
        self.assertEqual(report["effective_configuration"], {
            "repeated_failures_count": 2, "repeated_failures_window_seconds": 30,
            "success_after_failures_count": 2, "success_after_failures_window_seconds": 60,
            "multiple_accounts_count": 2, "multiple_accounts_window_seconds": 60,
        })
        self.assertEqual([(f["threshold_count"], f["window_seconds"]) for f in report["findings"]], [(2, 30), (2, 60), (2, 60)])
        self.assertEqual([f["event_count"] for f in report["findings"]], [2, 3, 2])
