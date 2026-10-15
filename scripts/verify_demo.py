"""Verify documented synthetic demos through the CLI; standard library only."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_FIELDS = (
    "parsed_events", "successful_logins", "failed_logins", "unique_ips",
    "unique_usernames", "ignored_blank_lines", "skipped_lines",
)
SUMMARY_LABELS = (
    "Parsed events", "Successful logins", "Failed logins", "Unique IPs",
    "Unique usernames", "Ignored blank lines", "Skipped nonblank lines",
)
# Fixed expectations from samples/README.md, not obtained from the analyzer.
SUMMARIES = {
    "sample.log": (9, 4, 5, 3, 5, 2, 4),
    "normal.log": (8, 6, 2, 3, 3, 0, 0),
    "suspicious.log": (14, 3, 11, 3, 7, 0, 0),
    "custom.log": (5, 1, 4, 2, 3, 0, 0),
}
DEFAULT_CONFIG = {
    "repeated_failures_count": 5, "repeated_failures_window_seconds": 300,
    "success_after_failures_count": 5, "success_after_failures_window_seconds": 600,
    "multiple_accounts_count": 5, "multiple_accounts_window_seconds": 600,
}
CUSTOM_CONFIG = {
    "repeated_failures_count": 2, "repeated_failures_window_seconds": 30,
    "success_after_failures_count": 2, "success_after_failures_window_seconds": 60,
    "multiple_accounts_count": 2, "multiple_accounts_window_seconds": 60,
}
# rule, IP, trigger line, complete evidence lines, threshold count, window seconds
FINDINGS = {
    "suspicious.log": [
        ("repeated_failures", "192.0.2.10", 5, [1, 2, 3, 4, 5], 5, 300),
        ("success_after_failures", "192.0.2.10", 6, [1, 2, 3, 4, 5, 6], 5, 600),
        ("success_after_failures", "192.0.2.10", 7, [1, 2, 3, 4, 5, 7], 5, 600),
        ("multiple_accounts", "198.51.100.20", 13, [9, 10, 11, 12, 13], 5, 600),
        ("multiple_accounts", "198.51.100.20", 14, [10, 11, 12, 13, 14], 5, 600),
    ],
    "custom.log": [
        ("repeated_failures", "192.0.2.10", 2, [1, 2], 2, 30),
        ("success_after_failures", "192.0.2.10", 3, [1, 2, 3], 2, 60),
        ("multiple_accounts", "198.51.100.20", 5, [4, 5], 2, 60),
    ],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_cli(arguments: list[str], name: str | None = None, count: int = 0) -> str:
    result = subprocess.run(
        [sys.executable, "loginwatch.py", *arguments], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", timeout=60,
    )
    require(result.returncode == 0, f"CLI failed for {arguments}: {result.stderr}")
    require(not result.stderr, f"Unexpected stderr for {arguments}: {result.stderr}")
    if name is not None:
        lines = result.stdout.splitlines()
        for label, value in zip(SUMMARY_LABELS, SUMMARIES[name]):
            require(f"{label}: {value}" in lines, f"Wrong summary: {name}, {label}")
        require(f"Findings: {count}" in lines, f"Wrong finding count: {name}")
    else:
        require("--config" in result.stdout and "--json" in result.stdout, "Incomplete help")
    return result.stdout


def verify_report(path: Path, name: str, config: dict[str, int]) -> None:
    payload = path.read_bytes()
    require(not payload.startswith(b"\xef\xbb\xbf") and b"\r" not in payload, "Wrong encoding/newlines")
    require(payload.endswith(b"\n") and not payload.endswith(b"\n\n"), "Wrong final newline")
    report = json.loads(payload.decode("utf-8"))
    require(set(report) == {"schema_version", "source_filename", "summary", "effective_configuration", "findings"}, "Wrong root fields")
    require(report["schema_version"] == "1.0" and report["source_filename"] == name, "Wrong schema/source")
    require(report["summary"] == dict(zip(SUMMARY_FIELDS, SUMMARIES[name])), "Wrong JSON summary")
    require(report["effective_configuration"] == config, "Wrong effective configuration")
    expected = FINDINGS[name]
    require(len(report["findings"]) == len(expected), "Wrong JSON finding count")
    raw_lines = (ROOT / "samples" / name).read_text(encoding="utf-8").splitlines()
    successes = {6, 7, 8} if name == "suspicious.log" else {3}
    for finding, (rule, ip, trigger, evidence, threshold, window) in zip(report["findings"], expected):
        require(set(finding) == {
            "id", "rule_id", "ip", "usernames", "trigger_timestamp", "evidence_start",
            "evidence_end", "event_count", "threshold_count", "window_seconds", "explanation", "evidence",
        }, "Wrong finding fields")
        require((finding["rule_id"], finding["ip"], finding["id"]) ==
                (rule, ip, f"{rule}:{ip}:line-{trigger}"), "Wrong finding order/identity")
        require((finding["threshold_count"], finding["window_seconds"], finding["event_count"]) ==
                (threshold, window, len(evidence)), "Wrong thresholds/event count")
        require([event["line_number"] for event in finding["evidence"]] == evidence, "Wrong evidence membership")
        require(finding["trigger_timestamp"] == raw_lines[trigger - 1].split()[0], "Wrong UTC trigger")
        require(finding["evidence_start"] == raw_lines[evidence[0] - 1].split()[0], "Wrong evidence start")
        require(finding["evidence_end"] == finding["trigger_timestamp"], "Wrong evidence end")
        require(finding["usernames"] == sorted({raw_lines[n - 1].split()[-6] for n in evidence}), "Wrong usernames")
        require(f"threshold: {threshold}" in finding["explanation"] and
                f"{window} seconds" in finding["explanation"], "Wrong threshold explanation")
        for event, number in zip(finding["evidence"], evidence):
            raw = raw_lines[number - 1]
            words = raw.split()  # These fixed synthetic fixtures use UTC/Z and the documented suffix.
            require(event == {
                "timestamp": words[0], "ip": words[-4], "username": words[-6],
                "result": "success" if number in successes else "failure",
                "line_number": number, "raw_line": raw,
            }, f"Wrong supporting event: {name}, line {number}")


def main() -> int:
    protected = list(ROOT.glob("*.py")) + list((ROOT / "samples").glob("*.log"))
    protected += list((ROOT / "samples").glob("*.json"))
    before = {path: path.read_bytes() for path in protected}
    for name, count in (("sample.log", 0), ("normal.log", 0), ("suspicious.log", 5), ("custom.log", 0)):
        run_cli([f"samples/{name}"], name, count)
        print(f"PASS {name}: summary and {count} findings")
    run_cli(["--help"])
    print("PASS --help")
    with tempfile.TemporaryDirectory(prefix="loginwatch-demo-") as directory:
        output_directory = Path(directory)
        for name, config, count in (("suspicious.log", DEFAULT_CONFIG, 5), ("custom.log", CUSTOM_CONFIG, 3)):
            output = output_directory / (name + ".json")
            arguments = [f"samples/{name}"]
            if name == "custom.log":
                arguments += ["--config", "samples/custom-config.json"]
            arguments += ["--json", str(output)]
            run_cli(arguments, name, count)
            verify_report(output, name, config)
            original = output.read_bytes()
            run_cli(arguments, name, count)
            require(output.read_bytes() == original, f"Non-reproducible JSON: {name}")
            require(not list(output_directory.glob(".loginwatch-*.tmp")), "Temporary export files remain")
            print(f"PASS {name}: full JSON/evidence, identical repeat bytes, no temporary export files")
    require(all(path.read_bytes() == original for path, original in before.items()), "Source/configuration changed")
    print("PASS source/configuration preservation; seven demo/help commands and two repeat exports")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Demo verification failed: {error}", file=sys.stderr)
        sys.exit(1)
