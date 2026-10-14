from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from loginwatch import main
from test_reporter import EXPECTED_SAMPLE_OUTPUT


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(ROOT / "loginwatch.py"), *map(str, arguments)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def assert_input_error(self, result, expected_message):
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn(expected_message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_documented_sample_command(self):
        path = ROOT / "samples" / "sample.log"
        original = path.read_bytes()
        result = self.run_cli("samples/sample.log")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, EXPECTED_SAMPLE_OUTPUT + "\n\nFindings: 0\n"
                         "No suspicious patterns detected by the three default rules.\n")
        self.assertEqual(path.read_bytes(), original)

    def test_empty_file_and_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty input.log"
            path.write_text("", encoding="utf-8")
            result = self.run_cli(path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(result.stdout, """LoginWatch activity summary
Parsed events: 0
Successful logins: 0
Failed logins: 0
Unique IPs: 0
Unique usernames: 0
Ignored blank lines: 0
Skipped nonblank lines: 0

Findings: 0
No suspicious patterns detected by the three default rules.
""")

    def test_unsupported_file_completes_with_zero_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsupported.log"
            path.write_text("unsupported\n\n", encoding="utf-8")
            result = self.run_cli(path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Parsed events: 0\n", result.stdout)
            self.assertIn("Ignored blank lines: 1\n", result.stdout)
            self.assertIn("Skipped nonblank lines: 1\n", result.stdout)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.log"
            result = self.run_cli(path)
            self.assert_input_error(result, "cannot read")
            self.assertIn(str(path), result.stderr)
            self.assertIn("readable file", result.stderr)

    def test_directory_input(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assert_input_error(self.run_cli(directory), "cannot read")

    def test_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.log"
            original = b"\xff\xfe"
            path.write_bytes(original)
            self.assert_input_error(self.run_cli(path), "provide a UTF-8 text file")
            self.assertEqual(path.read_bytes(), original)

    def test_invalid_utf8_after_valid_data_has_no_partial_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid_after_valid.log"
            original = (ROOT / "samples" / "suspicious.log").read_bytes() + b"\xff"
            path.write_bytes(original)
            self.assert_input_error(self.run_cli(path), "provide a UTF-8 text file")
            self.assertEqual(path.read_bytes(), original)

    def test_normal_demo(self):
        result = self.run_cli("samples/normal.log")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Parsed events: 8\nSuccessful logins: 6\nFailed logins: 2\n", result.stdout)
        self.assertIn("Findings: 0\n", result.stdout)

    def test_suspicious_demo_reports_reasons_and_supporting_lines(self):
        path = ROOT / "samples" / "suspicious.log"
        original = path.read_bytes()
        result = self.run_cli("samples/suspicious.log")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Parsed events: 14\nSuccessful logins: 3\nFailed logins: 11\n", result.stdout)
        self.assertIn("Findings: 5\n", result.stdout)
        self.assertEqual(result.stdout.count("Supporting source lines:"), 5)
        self.assertIn("[repeated_failures:192.0.2.10:line-5]", result.stdout)
        self.assertIn("[success_after_failures:192.0.2.10:line-6]", result.stdout)
        self.assertIn("[success_after_failures:192.0.2.10:line-7]", result.stdout)
        self.assertIn("[multiple_accounts:198.51.100.20:line-13]", result.stdout)
        self.assertIn("[multiple_accounts:198.51.100.20:line-14]", result.stdout)
        self.assertNotIn("  line 8:", result.stdout)
        self.assertIn("threshold: 5 failures", result.stdout)
        self.assertIn("threshold: 5 distinct usernames", result.stdout)
        self.assertEqual(path.read_bytes(), original)

    def test_permission_denied_without_platform_dependent_permissions(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("loginwatch.parse_file", side_effect=PermissionError(13, "Permission denied")):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main(["synthetic.log"])
        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Permission denied", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_help(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)
        self.assertIn("UTF-8 log file", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_missing_argument(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("required", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_future_phase_options_are_not_available(self):
        for option in ("--config", "--json"):
            with self.subTest(option=option):
                result = self.run_cli("samples/sample.log", option, "unused.json")
                self.assertEqual(result.returncode, 2)
                self.assertIn("unrecognized arguments", result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
