from dataclasses import asdict, replace
from pathlib import Path
import unittest

from analyzer import analyze
from configuration import DetectionConfig, MAX_CONFIG_INTEGER, load_config
from parser import parse_file
from test_analyzer import event, failures, source_lines


ROOT = Path(__file__).resolve().parents[1]


def selected(records, rule, config):
    return [finding for finding in analyze(records, config) if finding.rule_id == rule]


class ConfiguredAnalyzerTests(unittest.TestCase):
    def test_explicit_defaults_preserve_all_fixture_findings(self):
        for name in ("sample.log", "normal.log", "suspicious.log"):
            with self.subTest(name=name):
                records = parse_file(ROOT / "samples" / name).events
                self.assertEqual(analyze(records), analyze(records, DetectionConfig()))

    def test_each_custom_count_and_window_including_boundary_and_outside(self):
        for rule in ("repeated_failures", "success_after_failures", "multiple_accounts"):
            with self.subTest(rule=rule):
                config = replace(DetectionConfig(), **{rule + "_count": 2, rule + "_window_seconds": 10})
                if rule == "success_after_failures":
                    records = failures([0, 5]) + [event(10, 3, "success")]
                    outside = failures([0, 5]) + [event(10.000001, 3, "success")]
                    expected_lines = [1, 2, 3]
                else:
                    users = ["alice", "bob"] if rule == "multiple_accounts" else None
                    records = failures([0, 10], users)
                    outside = failures([0, 10.000001], users)
                    expected_lines = [1, 2]
                found = selected(records, rule, config)
                self.assertEqual(len(found), 1)
                self.assertEqual(source_lines(found[0]), expected_lines)
                self.assertEqual((found[0].threshold_count, found[0].window_seconds), (2, 10))
                self.assertIn("threshold: 2", found[0].explanation)
                self.assertIn("10 seconds", found[0].explanation)
                self.assertEqual(selected(outside, rule, config), [])

    def test_each_custom_rule_below_count_and_raised_count(self):
        for rule in ("repeated_failures", "success_after_failures", "multiple_accounts"):
            with self.subTest(rule=rule):
                config = replace(DetectionConfig(), **{rule + "_count": 6})
                records = failures(range(5), ["a", "b", "c", "d", "e"] if rule == "multiple_accounts" else None)
                if rule == "success_after_failures":
                    records.append(event(6, 6, "success"))
                self.assertEqual(selected(records, rule, config), [])

    def test_minimum_count_and_window_values(self):
        config = DetectionConfig(1, 1, 1, 1, 1, 1)
        found = analyze([event(0, 1), event(1, 2, "success")], config)
        self.assertEqual([f.rule_id for f in found], ["multiple_accounts", "repeated_failures", "success_after_failures"])
        self.assertEqual([source_lines(f) for f in found], [[1], [1], [1, 2]])

    def test_extreme_counts_and_windows_are_safe_and_quiet(self):
        config = DetectionConfig(**{key: MAX_CONFIG_INTEGER for key in asdict(DetectionConfig())})
        records = failures(range(8)) + [event(10, 9, "success")]
        self.assertEqual(analyze(records, config), ())

    def test_maximum_windows_with_extreme_supported_dates(self):
        config = DetectionConfig(2, MAX_CONFIG_INTEGER, 2, MAX_CONFIG_INTEGER, 2, MAX_CONFIG_INTEGER)
        records = [
            event(0, 1, timestamp="0001-01-01T00:00:00Z"),
            event(0, 2, timestamp="9999-12-31T23:59:58Z"),
            event(0, 3, "success", timestamp="9999-12-31T23:59:59Z"),
        ]
        self.assertEqual(analyze(records, config), ())

    def test_custom_failure_episodes_rearm_after_expiry(self):
        for rule in ("repeated_failures", "multiple_accounts"):
            with self.subTest(rule=rule):
                config = replace(DetectionConfig(), **{rule + "_count": 2, rule + "_window_seconds": 10})
                users = ["a", "b", "a"] if rule == "multiple_accounts" else None
                records = failures([0, 1, 10.000001], users)
                found = selected(records, rule, config)
                self.assertEqual([source_lines(f) for f in found], [[1, 2], [2, 3]])

    def test_custom_success_rule_keeps_same_ip_account_correlation(self):
        config = DetectionConfig(success_after_failures_count=2)
        records = failures([0, 1]) + [event(2, 3, "success", username="bob"),
                                             event(3, 4, "success", ip="198.51.100.20")]
        self.assertEqual(selected(records, "success_after_failures", config), [])

    def test_custom_fixture_matches_independent_documented_expectations(self):
        records = parse_file(ROOT / "samples" / "custom.log").events
        snapshot = tuple(records)
        config = load_config(ROOT / "samples" / "custom-config.json")
        self.assertEqual(analyze(records), ())
        found = analyze(records, config)
        self.assertEqual([(f.rule_id, source_lines(f), f.threshold_count, f.window_seconds) for f in found], [
            ("repeated_failures", [1, 2], 2, 30),
            ("success_after_failures", [1, 2, 3], 2, 60),
            ("multiple_accounts", [4, 5], 2, 60),
        ])
        self.assertEqual([f.id for f in found], ["repeated_failures:192.0.2.10:line-2",
                         "success_after_failures:192.0.2.10:line-3", "multiple_accounts:198.51.100.20:line-5"])
        self.assertEqual(records, snapshot)
