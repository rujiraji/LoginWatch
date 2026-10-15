"""Load and validate the immutable effective detection configuration."""

from dataclasses import dataclass, fields
import json
from pathlib import Path


MAX_CONFIG_INTEGER = 2_147_483_647


class ConfigurationError(ValueError):
    """A configuration cannot be read or violates the documented contract."""


@dataclass(frozen=True, slots=True)
class DetectionConfig:
    repeated_failures_count: int = 5
    repeated_failures_window_seconds: int = 300
    success_after_failures_count: int = 5
    success_after_failures_window_seconds: int = 600
    multiple_accounts_count: int = 5
    multiple_accounts_window_seconds: int = 600

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or not 1 <= value <= MAX_CONFIG_INTEGER:
                raise ConfigurationError(
                    f"'{field.name}' must be an integer in 1..{MAX_CONFIG_INTEGER} "
                    "(booleans are not integers)."
                )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError(f"duplicate configuration key '{key}'")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ConfigurationError(f"non-finite JSON constant '{value}' is not allowed")


def load_config(path: str | Path | None = None) -> DetectionConfig:
    if path is None:
        return DetectionConfig()
    try:
        with open(path, encoding="utf-8") as source:
            values = json.load(
                source, object_pairs_hook=_unique_object, parse_constant=_reject_constant
            )
    except UnicodeError as error:
        raise ConfigurationError(f"cannot decode configuration '{path}' as UTF-8") from error
    except OSError as error:
        raise ConfigurationError(
            f"cannot read configuration '{path}': {error.strerror or error}"
        ) from error
    except (ValueError, RecursionError) as error:
        raise ConfigurationError(f"invalid configuration '{path}': {error}") from error
    if not isinstance(values, dict):
        raise ConfigurationError("configuration must be a JSON object")
    unknown = values.keys() - {field.name for field in fields(DetectionConfig)}
    if unknown:
        raise ConfigurationError(f"unknown configuration fields: {', '.join(sorted(unknown))}")
    return DetectionConfig(**values)
