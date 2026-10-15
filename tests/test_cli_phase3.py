from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from loginwatch import main
import test_cli
from test_configuration import DEFAULTS


ROOT = Path(__file__).resolve().parents[1]


class Phase3CliTests(unittest.TestCase):
    run_cli = test_cli.CliTests.run_cli
    assert_input_error = test_cli.CliTests.assert_input_error

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.output = self.root / "report with spaces.json"
        self.config = self.root / "config.json"
        self.config.write_text("{}", encoding="utf-8")
        self.source = self.root / "synthetic.log"
        self.source.write_bytes((ROOT / "samples" / "custom.log").read_bytes())

    def assert_no_temporary_files(self):
        self.assertEqual(list(self.root.glob(".loginwatch-*.tmp")), [])

    def test_custom_demo_console_and_full_json(self):
        source = ROOT / "samples" / "custom.log"
        config = ROOT / "samples" / "custom-config.json"
        before = (source.read_bytes(), config.read_bytes())
        result = self.run_cli(source, "--config", config, "--json", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Findings: 3\n", result.stdout)
        self.assertIn("threshold: 2 failures", result.stdout)
        self.assertIn("threshold: 2 distinct usernames", result.stdout)
        self.assertNotIn("default rules", result.stdout)
        report = json.loads(self.output.read_bytes())
        self.assertEqual(report["source_filename"], "custom.log")
        self.assertEqual(report["summary"], {
            "parsed_events": 5, "successful_logins": 1, "failed_logins": 4,
            "unique_ips": 2, "unique_usernames": 3, "ignored_blank_lines": 0, "skipped_lines": 0,
        })
        self.assertEqual([(f["rule_id"], [e["line_number"] for e in f["evidence"]]) for f in report["findings"]], [
            ("repeated_failures", [1, 2]), ("success_after_failures", [1, 2, 3]), ("multiple_accounts", [4, 5]),
        ])
        self.assertEqual((source.read_bytes(), config.read_bytes()), before)
        self.assert_no_temporary_files()

    def test_partial_configuration_exports_all_effective_fields(self):
        self.config.write_text('{"repeated_failures_count": 2}', encoding="utf-8")
        result = self.run_cli(self.source, "--config", self.config, "--json", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(self.output.read_bytes())
        self.assertEqual(report["effective_configuration"], {**DEFAULTS, "repeated_failures_count": 2})
        self.assertEqual(len(report["findings"]), 2)

    def test_empty_object_and_omitted_config_produce_identical_bytes(self):
        first = self.run_cli(self.source, "--json", self.output)
        original = self.output.read_bytes()
        second = self.run_cli(self.source, "--config", self.config, "--json", self.output)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(first.stdout, second.stdout)

    def test_reproducible_bytes_across_processes_paths_and_destinations(self):
        first = self.run_cli("samples/suspicious.log", "--json", self.output)
        other_output = self.root / "other.json"
        second = self.run_cli(ROOT / "samples" / "suspicious.log", "--json", other_output)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        original = self.output.read_bytes()
        self.assertEqual(other_output.read_bytes(), original)
        self.assertFalse(original.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", original)
        self.assertTrue(original.endswith(b"\n"))
        self.assertEqual(len(json.loads(original)["findings"]), 5)

    def test_empty_and_normal_reports(self):
        empty = self.root / "empty.log"
        empty.write_bytes(b"")
        for source, count in ((empty, 0), (ROOT / "samples" / "normal.log", 8)):
            with self.subTest(source=source):
                result = self.run_cli(source, "--json", self.output)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(self.output.read_bytes())
                self.assertEqual(report["findings"], [])
                self.assertEqual(report["summary"]["parsed_events"], count)

    def test_existing_report_is_replaced_on_success(self):
        self.output.write_bytes(b"old report")
        result = self.run_cli(self.source, "--json", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.output.read_bytes())["schema_version"], "1.0")
        self.assert_no_temporary_files()

    def test_invalid_configs_leave_existing_report_and_inputs_untouched(self):
        invalid = (
            "{", "[]", "null", '{"unknown": 2}',
            '{"repeated_failures_count": true}', '{"repeated_failures_count": 0}',
            '{"repeated_failures_count": -1}', '{"repeated_failures_count": 2.0}',
            '{"repeated_failures_count": "2"}', '{"repeated_failures_window_seconds": 2147483648}',
            '{"multiple_accounts_count": 1, "multiple_accounts_count": 2}',
            '{"success_after_failures_count": NaN}',
        )
        original_source = self.source.read_bytes()
        for text in invalid:
            with self.subTest(text=text):
                self.config.write_text(text, encoding="utf-8")
                original_config = self.config.read_bytes()
                self.output.write_bytes(b"existing report")
                result = self.run_cli(self.source, "--config", self.config, "--json", self.output)
                self.assert_input_error(result, "LoginWatch:")
                self.assertEqual(self.output.read_bytes(), b"existing report")
                self.assertEqual(self.source.read_bytes(), original_source)
                self.assertEqual(self.config.read_bytes(), original_config)
                self.assert_no_temporary_files()

    def test_missing_directory_and_invalid_utf8_configs(self):
        missing = self.root / "missing.json"
        bad_encoding = self.root / "encoding.json"
        bad_encoding.write_bytes(b"\xff")
        for config in (missing, self.root, bad_encoding):
            with self.subTest(config=config):
                self.output.write_bytes(b"existing report")
                result = self.run_cli(self.source, "--config", config, "--json", self.output)
                self.assert_input_error(result, "configuration")
                self.assertEqual(self.output.read_bytes(), b"existing report")
                self.assert_no_temporary_files()

    def test_invalid_input_after_valid_config_preserves_existing_report(self):
        self.source.write_bytes(b"\xff")
        self.output.write_bytes(b"existing report")
        result = self.run_cli(self.source, "--config", self.config, "--json", self.output)
        self.assert_input_error(result, "UTF-8")
        self.assertEqual(self.output.read_bytes(), b"existing report")
        self.assertEqual(self.source.read_bytes(), b"\xff")
        self.assertEqual(self.config.read_bytes(), b"{}")
        self.assert_no_temporary_files()

    def test_missing_output_directory_and_directory_destination(self):
        for destination in (self.root / "missing" / "report.json", self.root):
            with self.subTest(destination=destination):
                result = self.run_cli(self.source, "--json", destination)
                self.assert_input_error(result, "cannot write JSON report")
                self.assert_no_temporary_files()

    def test_direct_input_and_config_path_collisions(self):
        before = (self.source.read_bytes(), self.config.read_bytes())
        for destination in (self.source, self.config, self.root / "." / self.source.name):
            with self.subTest(destination=destination):
                result = self.run_cli(self.source, "--config", self.config, "--json", destination)
                self.assert_input_error(result, "input log or configuration")
                self.assertEqual((self.source.read_bytes(), self.config.read_bytes()), before)
                self.assert_no_temporary_files()

    def test_hardlink_input_and_config_path_collisions(self):
        before = (self.source.read_bytes(), self.config.read_bytes())
        for target in (self.source, self.config):
            with self.subTest(target=target):
                try:
                    os.link(target, self.output)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f"hard links unavailable: {error}")
                result = self.run_cli(self.source, "--config", self.config, "--json", self.output)
                self.assert_input_error(result, "input log or configuration")
                self.assertEqual((self.source.read_bytes(), self.config.read_bytes()), before)
                self.output.unlink()
                self.assert_no_temporary_files()

    def test_symlink_input_and_config_path_collisions(self):
        before = (self.source.read_bytes(), self.config.read_bytes())
        for target in (self.source, self.config):
            with self.subTest(target=target):
                try:
                    self.output.symlink_to(target)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f"symlinks unavailable: {error}")
                result = self.run_cli(self.source, "--config", self.config, "--json", self.output)
                self.assert_input_error(result, "input log or configuration")
                self.assertEqual((self.source.read_bytes(), self.config.read_bytes()), before)
                self.output.unlink()
                self.assert_no_temporary_files()

    def test_replace_failure_cli_is_concise_and_preserves_existing_report(self):
        self.output.write_bytes(b"existing report")
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("report_export.os.replace", side_effect=PermissionError(13, "Permission denied")):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main([str(self.source), "--json", str(self.output)])
        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("cannot write JSON report", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(self.output.read_bytes(), b"existing report")
        self.assert_no_temporary_files()

    def test_config_permission_failure_cli_is_concise(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("configuration.open", side_effect=PermissionError(13, "Permission denied")):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main([str(self.source), "--config", str(self.config)])
        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("cannot read configuration", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
