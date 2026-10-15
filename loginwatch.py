"""Coordinate input parsing, activity summary, and Phase 2 detection."""

import argparse
from pathlib import Path
import sys

from analyzer import analyze
from parser import parse_file
from reporter import format_findings, format_summary, summarize


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(
        description="Summarize SSH password-login activity and detect suspicious "
        "patterns in a UTF-8 log file."
    )
    cli.add_argument("path", type=Path, help="path to the input log file")
    args = cli.parse_args(argv)
    try:
        parsed = parse_file(args.path)
    except UnicodeDecodeError:
        print(
            f"LoginWatch: cannot decode '{args.path}' as UTF-8; provide a UTF-8 text file.",
            file=sys.stderr,
        )
        return 1
    except OSError as error:
        print(
            f"LoginWatch: cannot read '{args.path}': {error.strerror or error}. "
            "Check that the path names a readable file.",
            file=sys.stderr,
        )
        return 1
    print(format_summary(summarize(parsed)))
    print()
    print(format_findings(analyze(parsed.events)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
