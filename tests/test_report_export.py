import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from report_export import ExportError, write_report


class ReportExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source.log"
        self.config = self.root / "config.json"
        self.output = self.root / "report.json"
        self.source.write_bytes(b"synthetic input\r\n")
        self.config.write_bytes(b"{}\r\n")

    def assert_sources_preserved_and_no_temporary_files(self):
        self.assertEqual(self.source.read_bytes(), b"synthetic input\r\n")
        self.assertEqual(self.config.read_bytes(), b"{}\r\n")
        self.assertEqual(list(self.root.glob(".loginwatch-*.tmp")), [])

    def export(self, text='{"message": "josé"}\n'):
        write_report(self.output, text, [self.source, self.config])

    def symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symlinks unavailable: {error}")

    def hardlink(self, path, target):
        try:
            os.link(target, path)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"hard links unavailable: {error}")

    def test_utf8_bytes_without_bom_and_sources_preserved(self):
        self.export()
        self.assertEqual(self.output.read_bytes(), '{"message": "josé"}\n'.encode("utf-8"))
        self.assert_sources_preserved_and_no_temporary_files()

    def test_success_replaces_existing_report(self):
        self.output.write_bytes(b"old report")
        self.export("new report\n")
        self.assertEqual(self.output.read_bytes(), b"new report\n")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_temporary_file_is_in_destination_directory_and_closed_before_replace(self):
        replace = os.replace
        observed = []

        def verify_replace(source, destination):
            self.assertEqual(Path(source).parent, self.output.parent)
            self.assertEqual(Path(source).read_bytes(), b"complete\n")
            # Windows replacement also verifies the temporary handle is closed.
            observed.append(source)
            return replace(source, destination)

        with patch("report_export.os.replace", side_effect=verify_replace):
            self.export("complete\n")
        self.assertEqual(len(observed), 1)
        self.assert_sources_preserved_and_no_temporary_files()

    def test_direct_and_relative_input_and_config_collisions(self):
        for target in (self.source, self.config, self.root / "subdir" / ".." / "source.log"):
            with self.subTest(target=target), self.assertRaisesRegex(ExportError, "input log or configuration"):
                write_report(target, "unsafe", [self.source, self.config])
        self.assert_sources_preserved_and_no_temporary_files()

    def test_hardlink_input_collision(self):
        self.hardlink(self.output, self.source)
        with self.assertRaisesRegex(ExportError, "input log or configuration"):
            self.export()
        self.assert_sources_preserved_and_no_temporary_files()

    def test_hardlink_configuration_collision(self):
        self.hardlink(self.output, self.config)
        with self.assertRaisesRegex(ExportError, "input log or configuration"):
            self.export()
        self.assert_sources_preserved_and_no_temporary_files()

    def test_symlink_input_and_config_collisions(self):
        for target in (self.source, self.config):
            with self.subTest(target=target):
                self.symlink(self.output, target)
                with self.assertRaisesRegex(ExportError, "input log or configuration"):
                    self.export()
                self.assertTrue(self.output.is_symlink())
                self.output.unlink()
        self.assert_sources_preserved_and_no_temporary_files()

    def test_symlink_parent_directory_collision(self):
        linked_directory = self.root / "linked"
        self.symlink(linked_directory, self.root, directory=True)
        with self.assertRaisesRegex(ExportError, "input log or configuration"):
            write_report(linked_directory / self.source.name, "unsafe", [self.source, self.config])
        self.assert_sources_preserved_and_no_temporary_files()

    def test_unrelated_report_symlink_entry_is_replaced_without_writing_target(self):
        old_target = self.root / "old-target.json"
        old_target.write_bytes(b"untouched target")
        self.symlink(self.output, old_target)
        self.export("new report\n")
        self.assertFalse(self.output.is_symlink())
        self.assertEqual(self.output.read_bytes(), b"new report\n")
        self.assertEqual(old_target.read_bytes(), b"untouched target")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_replace_failure_preserves_existing_report_and_removes_temporary_file(self):
        self.output.write_bytes(b"existing report")
        with patch("report_export.os.replace", side_effect=PermissionError(13, "Permission denied")):
            with self.assertRaisesRegex(ExportError, "cannot write JSON report"):
                self.export()
        self.assertEqual(self.output.read_bytes(), b"existing report")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_fsync_failure_preserves_existing_report_and_cleans_up(self):
        self.output.write_bytes(b"existing report")
        with patch("report_export.os.fsync", side_effect=OSError(28, "No space left")):
            with self.assertRaisesRegex(ExportError, "No space left"):
                self.export()
        self.assertEqual(self.output.read_bytes(), b"existing report")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_partial_write_failure_preserves_existing_report_and_cleans_up(self):
        self.output.write_bytes(b"existing report")
        factory = tempfile.NamedTemporaryFile

        def failing_factory(*args, **kwargs):
            handle = factory(*args, **kwargs)
            write = handle.write

            def partial_write(payload):
                write(payload[:5])
                raise OSError(28, "No space left during write")

            handle.write = partial_write
            return handle

        with patch("report_export.tempfile.NamedTemporaryFile", side_effect=failing_factory):
            with self.assertRaisesRegex(ExportError, "No space left during write"):
                self.export()
        self.assertEqual(self.output.read_bytes(), b"existing report")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_temporary_file_creation_failure_leaves_existing_report(self):
        self.output.write_bytes(b"existing report")
        with patch("report_export.tempfile.NamedTemporaryFile", side_effect=PermissionError(13, "Permission denied")):
            with self.assertRaises(ExportError):
                self.export()
        self.assertEqual(self.output.read_bytes(), b"existing report")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_missing_destination_directory_is_not_created(self):
        missing = self.root / "missing"
        with self.assertRaisesRegex(ExportError, "cannot write JSON report"):
            write_report(missing / "report.json", "report", [self.source])
        self.assertFalse(missing.exists())
        self.assert_sources_preserved_and_no_temporary_files()

    def test_directory_destination_and_contents_are_preserved(self):
        self.output.mkdir()
        sentinel = self.output / "sentinel.txt"
        sentinel.write_bytes(b"untouched")
        with self.assertRaises(ExportError):
            self.export()
        self.assertEqual(sentinel.read_bytes(), b"untouched")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_invalid_path_and_unencodable_payload_are_clear_errors(self):
        with self.assertRaises(ExportError):
            write_report(str(self.root / "bad") + "\x00.json", "report", [self.source])
        self.output.write_bytes(b"existing report")
        with self.assertRaises(ExportError):
            self.export("\ud800")
        self.assertEqual(self.output.read_bytes(), b"existing report")
        self.assert_sources_preserved_and_no_temporary_files()

    def test_destination_is_checked_again_before_replace(self):
        def introduce_alias(_descriptor):
            self.hardlink(self.output, self.source)

        with patch("report_export.os.fsync", side_effect=introduce_alias):
            with self.assertRaisesRegex(ExportError, "input log or configuration"):
                self.export()
        self.assert_sources_preserved_and_no_temporary_files()
