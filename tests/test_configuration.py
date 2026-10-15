from dataclasses import FrozenInstanceError, asdict, fields
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from configuration import ConfigurationError, DetectionConfig, MAX_CONFIG_INTEGER, load_config


DEFAULTS = {
    "repeated_failures_count": 5,
    "repeated_failures_window_seconds": 300,
    "success_after_failures_count": 5,
    "success_after_failures_window_seconds": 600,
    "multiple_accounts_count": 5,
    "multiple_accounts_window_seconds": 600,
}


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "configuration.json"

    def load_text(self, text):
        self.path.write_text(text, encoding="utf-8")
        return load_config(self.path)

    def test_no_file_uses_exact_defaults(self):
        self.assertEqual(asdict(load_config()), DEFAULTS)

    def test_empty_object_uses_defaults(self):
        self.assertEqual(asdict(self.load_text("{}")), DEFAULTS)

    def test_partial_config_preserves_omitted_defaults(self):
        config = self.load_text('{"repeated_failures_count": 2, "multiple_accounts_window_seconds": 10}')
        self.assertEqual(asdict(config), {**DEFAULTS, "repeated_failures_count": 2,
                                         "multiple_accounts_window_seconds": 10})

    def test_all_fields_and_minimum_and_maximum_values(self):
        for value in (1, MAX_CONFIG_INTEGER):
            with self.subTest(value=value):
                expected = {key: value for key in DEFAULTS}
                self.assertEqual(asdict(self.load_text(json.dumps(expected))), expected)

    def test_config_is_immutable(self):
        config = load_config()
        with self.assertRaises(FrozenInstanceError):
            config.repeated_failures_count = 2

    def test_every_field_rejects_invalid_types_and_ranges(self):
        for field in fields(DetectionConfig):
            for value in (True, False, 0, -1, 1.0, 2.5, "5", None, [], {}, MAX_CONFIG_INTEGER + 1, 10**100):
                with self.subTest(field=field.name, value=value):
                    with self.assertRaisesRegex(ConfigurationError, "integer in 1..2147483647"):
                        self.load_text(json.dumps({field.name: value}))

    def test_direct_configuration_construction_also_validates(self):
        with self.assertRaises(ConfigurationError):
            DetectionConfig(repeated_failures_window_seconds=10**100)
        with self.assertRaises(ConfigurationError):
            DetectionConfig(success_after_failures_count=True)

    def test_non_object_roots(self):
        for text in ("[]", "null", '"text"', "true", "42", "2.5"):
            with self.subTest(text=text), self.assertRaisesRegex(ConfigurationError, "JSON object"):
                self.load_text(text)

    def test_unknown_fields(self):
        with self.assertRaisesRegex(ConfigurationError, "unknown configuration fields: other"):
            self.load_text('{"other": 5}')

    def test_duplicate_keys_including_nested_and_escaped_keys(self):
        texts = (
            '{"repeated_failures_count": 2, "repeated_failures_count": 3}',
            '{"other": {"nested": 1, "nested": 2}}',
            r'{"repeated_failures_count": 2, "repeated\u005ffailures_count": 3}',
        )
        for text in texts:
            with self.subTest(text=text), self.assertRaisesRegex(ConfigurationError, "duplicate configuration key"):
                self.load_text(text)

    def test_malformed_json(self):
        for text in ("", "{", '{"repeated_failures_count": 2,}', "{} {}", "// comment\n{}"):
            with self.subTest(text=text), self.assertRaisesRegex(ConfigurationError, "invalid configuration"):
                self.load_text(text)

    def test_non_finite_constants_are_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), self.assertRaisesRegex(ConfigurationError, "non-finite"):
                self.load_text('{"repeated_failures_count": ' + token + "}")

    def test_excessively_nested_json_is_a_configuration_error(self):
        # Python versions differ in decoder recursion limits; either decoding
        # or root-type validation must reject this without leaking an exception.
        with self.assertRaises(ConfigurationError):
            self.load_text("[" * 2000 + "0" + "]" * 2000)

    def test_decoder_recursion_error_is_reported_as_configuration_error(self):
        self.path.write_text("{}", encoding="utf-8")
        with patch("configuration.json.load", side_effect=RecursionError("too deeply nested")):
            with self.assertRaisesRegex(ConfigurationError, "invalid configuration"):
                load_config(self.path)

    def test_extremely_long_integer_is_a_configuration_error(self):
        with self.assertRaises(ConfigurationError):
            self.load_text('{"repeated_failures_count": ' + "9" * 5000 + "}")

    def test_missing_file_directory_and_permission_errors(self):
        with self.assertRaisesRegex(ConfigurationError, "cannot read configuration"):
            load_config(self.path)
        with self.assertRaisesRegex(ConfigurationError, "cannot read configuration"):
            load_config(self.path.parent)
        with patch("configuration.open", side_effect=PermissionError(13, "Permission denied")):
            with self.assertRaisesRegex(ConfigurationError, "Permission denied"):
                load_config(self.path)

    def test_invalid_utf8_and_file_preservation(self):
        original = b'{"repeated_failures_count": 2}\xff'
        self.path.write_bytes(original)
        with self.assertRaisesRegex(ConfigurationError, "as UTF-8"):
            load_config(self.path)
        self.assertEqual(self.path.read_bytes(), original)

    def test_success_does_not_modify_file(self):
        original = b'{\r\n  "repeated_failures_count": 2\r\n}\r\n'
        self.path.write_bytes(original)
        self.assertEqual(load_config(self.path).repeated_failures_count, 2)
        self.assertEqual(self.path.read_bytes(), original)
