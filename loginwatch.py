"""Coordinate configuration, input parsing, detection, and report delivery."""

import argparse
from pathlib import Path
import sys

from analyzer import analyze
from configuration import ConfigurationError, load_config
from parser import parse_file
from report_export import ExportError, write_report
from reporter import format_findings, format_json_report, format_summary, summarize


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(
        description="Summarize SSH password-login activity and detect suspicious "
        "patterns in a UTF-8 log file."
    )
    cli.add_argument("path", type=Path, help="path to the input log file")
    cli.add_argument("--config", type=Path, help="optional UTF-8 JSON detection configuration")
    cli.add_argument("--json", type=Path, help="atomically write a UTF-8 JSON report (replaces existing report)")
    args = cli.parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigurationError as error:
        print(f"LoginWatch: {error}", file=sys.stderr)
        return 1
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
    summary = summarize(parsed)
    findings = analyze(parsed.events, config)
    if args.json is not None:
        protected = [args.path]
        if args.config is not None:
            protected.append(args.config)
        try:
            write_report(args.json, format_json_report(args.path, summary, config, findings), protected)
        except ExportError as error:
            print(f"LoginWatch: {error}", file=sys.stderr)
            return 1
    print(format_summary(summary))
    print()
    print(format_findings(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
