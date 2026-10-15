"""Atomic UTF-8 export, protecting source files against path aliases."""

import os
from pathlib import Path
import tempfile
from typing import Iterable


class ExportError(Exception):
    """The report could not be safely written."""


def _check_destination(destination: Path, protected_paths: tuple[Path, ...]) -> None:
    resolved = destination.resolve()
    for protected in protected_paths:
        if resolved == protected.resolve():
            raise ExportError("JSON output must not refer to the input log or configuration")
        try:
            aliases_source = destination.samefile(protected)
        except FileNotFoundError:
            aliases_source = False
        if aliases_source:
            raise ExportError("JSON output must not refer to the input log or configuration")


def write_report(
    destination: str | Path, text: str, protected_paths: Iterable[str | Path]
) -> None:
    """Replace only after the new report is complete; never write through a symlink."""
    destination = Path(destination)
    protected = tuple(Path(path) for path in protected_paths)
    temporary_path = None
    try:
        _check_destination(destination, protected)
        payload = text.encode("utf-8")
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=".loginwatch-", suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        _check_destination(destination, protected)
        os.replace(temporary_path, destination)
        temporary_path = None
    except (OSError, ValueError, RuntimeError) as error:
        raise ExportError(f"cannot write JSON report '{destination}': {error}") from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as error:
                raise ExportError(
                    f"cannot clean up temporary report '{temporary_path}': {error}"
                ) from error
