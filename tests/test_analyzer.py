from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from analyzer import analyze
from parser import parse_file, parse_line
from reporter import summarize
from models import ActivitySummary


ROOT = Path(__file__).resolve().parents[1]
BASE = datetime(2026, 10, 11, 10, tzinfo=timezone.utc)


def event(seconds, line, result="failure", ip="192.0.2.10", username="alice", timestamp=None):
    timestamp = timestamp or (BASE + timedelta(seconds=seconds)).isoformat()
    verb = "Failed" if result == "failure" else "Accepted"
    raw = f"{timestamp} server sshd[1]: {verb} password for {username} from {ip} port 50000 ssh2"
    parsed = parse_line(raw, line)
    if parsed is None:
        raise AssertionError(f"Invalid synthetic test record: {raw}")
    return parsed


def failures(times, usernames=None):
    return [event(seconds, i + 1, username=usernames[i] if usernames else "alice")
            for i, seconds in enumerate(times)]


def for_rule(events, rule):
    return [finding for finding in analyze(events) if finding.rule_id == rule]


def source_lines(finding):
    return [record.line_number for record in finding.evidence]


class AnalyzerTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(analyze([]), ())

    def test_successes_only(self):
        self.assertEqual(analyze([event(i, i + 1, "success") for i in range(8)]), ())

    def test_repeated_failures_exact_threshold_and_boundary(self):
        records = failures([0, 60, 120, 180, 300])
        found = for_rule(records, "repeated_failures")
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.evidence, tuple(records))
        self.assertEqual(finding.event_count, 5)
        self.assertEqual(finding.usernames, ("alice",))
        self.assertEqual(finding.trigger_timestamp, BASE + timedelta(seconds=300))
        self.assertEqual(finding.evidence_start, BASE)
        self.assertEqual(finding.evidence_end, finding.trigger_timestamp)
        self.assertEqual((finding.threshold_count, finding.window_seconds), (5, 300))

    def test_repeated_failures_below_threshold(self):
        self.assertEqual(for_rule(failures([0, 1, 2, 3]), "repeated_failures"), [])

    def test_repeated_failures_just_outside_boundary(self):
        self.assertEqual(for_rule(failures([0, 60, 120, 180, 300.000001]), "repeated_failures"), [])

    def test_repeated_failures_group_by_ip_and_ignore_successes(self):
        records = failures([0, 1, 2, 3])
        records.extend([event(4, 5, "success"), event(5, 6, ip="198.51.100.20")])
        self.assertEqual(for_rule(records, "repeated_failures"), [])

    def test_repeated_failures_can_involve_different_accounts(self):
        records = failures(range(5), ["alice", "bob", "carol", "alice", "bob"])
        found = for_rule(records, "repeated_failures")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].usernames, ("alice", "bob", "carol"))

    def test_repeated_failures_suppression_keeps_trigger_snapshot(self):
        found = for_rule(failures(range(8)), "repeated_failures")
        self.assertEqual(len(found), 1)
        self.assertEqual(source_lines(found[0]), [1, 2, 3, 4, 5])

    def test_repeated_failures_rearms_before_new_failure_restores_threshold(self):
        found = for_rule(failures([0, 1, 2, 3, 4, 300.000001]), "repeated_failures")
        self.assertEqual([source_lines(f) for f in found], [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]])

    def test_repeated_failures_exact_boundary_does_not_rearm(self):
        found = for_rule(failures([0, 1, 2, 3, 4, 300]), "repeated_failures")
        self.assertEqual(len(found), 1)

    def test_repeated_failures_rearms_after_long_silent_gap(self):
        found = for_rule(failures([0, 1, 2, 3, 4, 1000, 1001, 1002, 1003, 1004]), "repeated_failures")
        self.assertEqual([source_lines(f) for f in found], [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]])

    def test_expiry_above_threshold_does_not_rearm(self):
        times = [0] * 5 + [1] * 5 + [300.000001]
        for rule in ("repeated_failures", "multiple_accounts"):
            with self.subTest(rule=rule):
                users = ["a", "b", "c", "d", "e"] * 2 + ["a"]
                # Use the matching window to expire the first five observations.
                adjusted = times if rule == "repeated_failures" else times[:-1] + [600.000001]
                self.assertEqual(len(for_rule(failures(adjusted, users), rule)), 1)

    def test_multiple_accounts_exact_threshold_and_boundary(self):
        records = failures([0, 150, 300, 450, 600], ["e", "d", "c", "b", "a"])
        found = for_rule(records, "multiple_accounts")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].evidence, tuple(records))
        self.assertEqual(found[0].usernames, ("a", "b", "c", "d", "e"))
        self.assertEqual((found[0].threshold_count, found[0].window_seconds), (5, 600))

    def test_multiple_accounts_just_outside_boundary(self):
        records = failures([0, 150, 300, 450, 600.000001], ["a", "b", "c", "d", "e"])
        self.assertEqual(for_rule(records, "multiple_accounts"), [])

    def test_multiple_accounts_counts_distinct_failure_users_only(self):
        records = failures(range(8), ["a", "b", "c", "d"] * 2)
        records.extend([event(8, 9, "success", username="e"), event(9, 10, username="e", ip="198.51.100.20")])
        self.assertEqual(for_rule(records, "multiple_accounts"), [])

    def test_multiple_accounts_usernames_are_case_sensitive(self):
        records = failures(range(5), ["alice", "Alice", "bob", "carol", "dave"])
        self.assertEqual(len(for_rule(records, "multiple_accounts")), 1)

    def test_multiple_accounts_suppression_and_full_failure_evidence(self):
        records = failures(range(7), ["a", "a", "b", "c", "d", "e", "f"])
        found = for_rule(records, "multiple_accounts")
        self.assertEqual(len(found), 1)
        self.assertEqual(source_lines(found[0]), [1, 2, 3, 4, 5, 6])
        self.assertEqual(found[0].event_count, 6)

    def test_multiple_accounts_rearms_before_new_failure_restores_threshold(self):
        records = failures([0, 1, 2, 3, 4, 600.000001], ["a", "b", "c", "d", "e", "a"])
        found = for_rule(records, "multiple_accounts")
        self.assertEqual([source_lines(f) for f in found], [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]])

    def test_multiple_accounts_exact_boundary_does_not_rearm(self):
        records = failures([0, 1, 2, 3, 4, 600], ["a", "b", "c", "d", "e", "a"])
        self.assertEqual(len(for_rule(records, "multiple_accounts")), 1)

    def test_multiple_accounts_rearms_after_long_silent_gap(self):
        records = failures([0, 1, 2, 3, 4, 1000, 1001, 1002, 1003, 1004], ["a", "b", "c", "d", "e"] * 2)
        found = for_rule(records, "multiple_accounts")
        self.assertEqual([source_lines(f) for f in found], [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]])

    def test_success_exact_threshold_and_boundary(self):
        records = failures([0, 100, 200, 300, 400]) + [event(600, 6, "success")]
        found = for_rule(records, "success_after_failures")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].evidence, tuple(records))
        self.assertEqual(found[0].event_count, 6)
        self.assertEqual(found[0].usernames, ("alice",))
        self.assertEqual((found[0].threshold_count, found[0].window_seconds), (5, 600))

    def test_success_just_outside_boundary(self):
        records = failures([0, 100, 200, 300, 400]) + [event(600.000001, 6, "success")]
        self.assertEqual(for_rule(records, "success_after_failures"), [])

    def test_success_below_threshold(self):
        records = failures(range(4)) + [event(4, 5, "success")]
        self.assertEqual(for_rule(records, "success_after_failures"), [])

    def test_success_requires_same_ip_and_case_sensitive_account(self):
        records = failures(range(5)) + [
            event(5, 6, "success", username="bob"),
            event(6, 7, "success", ip="198.51.100.20"),
            event(7, 8, "success", username="Alice"),
        ]
        self.assertEqual(for_rule(records, "success_after_failures"), [])

    def test_ip_wide_failures_do_not_satisfy_same_account_rule(self):
        records = failures(range(5), ["a", "b", "c", "d", "e"]) + [event(5, 6, "success", username="a")]
        self.assertEqual(for_rule(records, "success_after_failures"), [])

    def test_repeated_successes_have_separate_evidence_and_ids(self):
        records = failures(range(5)) + [event(5, 6, "success"), event(5, 7, "success")]
        found = for_rule(records, "success_after_failures")
        self.assertEqual([source_lines(f) for f in found], [[1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 7]])
        self.assertNotEqual(found[0].id, found[1].id)

    def test_success_evidence_excludes_expired_and_unrelated_records(self):
        records = failures([0, 100, 200, 300, 400, 500]) + [
            event(550, 7, username="bob"),
            event(560, 8, ip="198.51.100.20"),
            event(570, 9, "success"),
            event(650, 10, "success"),
        ]
        found = for_rule(records, "success_after_failures")
        self.assertEqual(source_lines(found[-1]), [2, 3, 4, 5, 6, 10])
        self.assertEqual(found[-1].event_count, 6)

    def test_ipv6_equivalent_spellings_share_detection_group(self):
        records = [event(i, i + 1, ip="2001:0DB8::1" if i % 2 else "2001:db8::1") for i in range(5)]
        found = for_rule(records, "repeated_failures")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].ip, "2001:db8::1")

    def test_equal_timestamps_use_source_lines_not_supplied_order(self):
        records = failures([0] * 5) + [event(0, 6, "success")]
        found = for_rule(reversed(records), "success_after_failures")
        self.assertEqual([source_lines(f) for f in found], [[1, 2, 3, 4, 5, 6]])
        earlier_success = [event(0, 1, "success")] + [event(0, i) for i in range(2, 7)]
        self.assertEqual(for_rule(reversed(earlier_success), "success_after_failures"), [])

    def test_equal_timestamp_failure_after_success_cannot_contribute(self):
        records = failures([0] * 4) + [event(0, 5, "success"), event(0, 6)]
        self.assertEqual(for_rule(records, "success_after_failures"), [])

    def test_out_of_order_and_equivalent_offsets_preserve_input(self):
        records = [
            event(0, 1, timestamp="2026-10-11T05:00:00-05:00"),
            event(0, 2, timestamp="2026-10-11T12:00:00+02:00"),
            event(0, 3, timestamp="2026-10-11T10:00:00Z"),
            event(0, 4, timestamp="2026-10-11T10:00:00+00:00"),
            event(0, 5, timestamp="2026-10-11T12:00:00+0200"),
            event(1, 6, "success"),
        ]
        unordered = [records[5], records[2], records[0], records[4], records[1], records[3]]
        snapshot = tuple(unordered)
        self.assertEqual(analyze(unordered), analyze(records))
        self.assertEqual(tuple(unordered), snapshot)
        self.assertTrue(all(a is b for a, b in zip(unordered, snapshot)))

    def test_interleaved_unrelated_events_do_not_reset_windows(self):
        records = failures([0, 10, 20, 30, 40]) + [event(50, 20, "success")]
        baseline = analyze(records)
        records += [event(i * 10 + 5, i + 10, "success", "198.51.100.20", "observer") for i in range(5)]
        self.assertEqual(analyze(records), baseline)
        distinct = failures([0, 10, 20, 30, 40], ["a", "b", "c", "d", "e"])
        self.assertEqual(for_rule(distinct + records[6:], "multiple_accounts"), for_rule(distinct, "multiple_accounts"))

    def test_suppression_is_independent_per_ip(self):
        records = failures(range(6)) + [event(i, i + 10, ip="198.51.100.20") for i in range(6)]
        found = for_rule(records, "repeated_failures")
        self.assertEqual([finding.ip for finding in found], ["192.0.2.10", "198.51.100.20"])

    def test_findings_are_deterministic_and_ordered_by_rule_then_group(self):
        records = failures([0] * 5, ["a", "b", "c", "d", "e"])
        records += [event(0, i + 10, ip="198.51.100.20", username=str(i)) for i in range(5)]
        expected = analyze(records)
        self.assertEqual(analyze(iter(reversed(records))), expected)
        self.assertEqual([(f.rule_id, f.ip) for f in expected], [
            ("multiple_accounts", "192.0.2.10"), ("multiple_accounts", "198.51.100.20"),
            ("repeated_failures", "192.0.2.10"), ("repeated_failures", "198.51.100.20"),
        ])
        self.assertEqual(len({f.id for f in expected}), len(expected))
        self.assertEqual(expected[0].id, "multiple_accounts:192.0.2.10:line-5")

    def test_duplicate_records_on_different_lines_are_observations(self):
        found = for_rule(failures([0] * 5), "repeated_failures")
        self.assertEqual(source_lines(found[0]), [1, 2, 3, 4, 5])
        self.assertEqual(len({record.raw_line for record in found[0].evidence}), 1)

    def test_original_and_normal_fixtures_have_no_findings(self):
        for name in ("sample.log", "normal.log"):
            with self.subTest(name=name):
                self.assertEqual(analyze(parse_file(ROOT / "samples" / name).events), ())
        normal = parse_file(ROOT / "samples" / "normal.log")
        self.assertEqual(summarize(normal), ActivitySummary(8, 6, 2, 3, 3, 0, 0))

    def test_suspicious_fixture_matches_independent_documented_expectations(self):
        parsed = parse_file(ROOT / "samples" / "suspicious.log")
        self.assertEqual(summarize(parsed), ActivitySummary(14, 3, 11, 3, 7, 0, 0))
        found = analyze(parsed.events)
        self.assertEqual([(f.rule_id, f.ip, f.trigger_timestamp, source_lines(f)) for f in found], [
            ("repeated_failures", "192.0.2.10", BASE + timedelta(seconds=300), [1, 2, 3, 4, 5]),
            ("success_after_failures", "192.0.2.10", BASE + timedelta(seconds=301), [1, 2, 3, 4, 5, 6]),
            ("success_after_failures", "192.0.2.10", BASE + timedelta(seconds=302), [1, 2, 3, 4, 5, 7]),
            ("multiple_accounts", "198.51.100.20", BASE + timedelta(seconds=1800), [9, 10, 11, 12, 13]),
            ("multiple_accounts", "198.51.100.20", BASE + timedelta(seconds=1801), [10, 11, 12, 13, 14]),
        ])
        self.assertEqual([f.event_count for f in found], [5, 6, 6, 5, 5])
        self.assertEqual([f.evidence_start for f in found], [BASE, BASE, BASE, BASE + timedelta(seconds=1200), BASE + timedelta(seconds=1380)])
        self.assertTrue(all(f.evidence_end == f.trigger_timestamp for f in found))
        self.assertEqual(found[-1].usernames, ("admin", "backup", "guest", "root", "service"))
