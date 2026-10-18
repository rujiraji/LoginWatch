# LoginWatch

LoginWatch is a standard-library Python CLI for reviewing SSH password-login
logs. It summarizes activity and explains repeated failures, success after
failures, and failures across multiple accounts using supporting source lines.
Findings are investigation signals, not proof of compromise.

All four planned phases are **Accepted and complete**. LoginWatch is
**release-ready and unpublished**; PR #4 awaits the owner's final merge.
No tag or GitHub release has been published. Acceptance and verification
history are in [docs/PLAN.md](docs/PLAN.md).

## Quick start

Use Python 3.11+ from the repository root. No package installation is needed.

```bash
python loginwatch.py samples/sample.log
python -m unittest discover -s tests
```

The synthetic sample produces this exact output:

```text
LoginWatch activity summary
Parsed events: 9
Successful logins: 4
Failed logins: 5
Unique IPs: 3
Unique usernames: 5
Ignored blank lines: 2
Skipped nonblank lines: 4

Findings: 0
No suspicious patterns detected by the three rules.
```

## Working examples

```bash
python loginwatch.py samples/normal.log
python loginwatch.py samples/suspicious.log
python loginwatch.py samples/custom.log
python loginwatch.py samples/custom.log --config samples/custom-config.json --json custom-report.json
python loginwatch.py samples/suspicious.log --json suspicious-report.json
python loginwatch.py --help
python scripts/verify_demo.py
```

Normal activity has zero findings. The suspicious example has five. Custom
configuration changes the custom example from zero findings to three.
[The walkthrough](docs/WALKTHROUGH.md) explains every trigger and evidence
set; [fixture expectations](samples/README.md) specify the counts independently.
The verification script checks the examples, repeats both exports to compare
bytes, and uses temporary reports without replacing files in the checkout.

## Architecture and contracts

The CLI validates configuration, parses the input into immutable events,
analyzes a view sorted by UTC timestamp/source line, and sends summaries and
findings to the reporter. Optional JSON export completes before console output.
Parsing, configuration, detection, formatting, and file replacement have
separate modules. [Architecture and interview notes](docs/ARCHITECTURE.md)
describe their inputs, outputs, and tradeoffs.

`--config` accepts partial UTF-8 JSON objects; omitted fields use defaults.
All six count/window values must be integers in `1..2147483647`. Duplicate or
unknown keys and invalid types/values are rejected. See
[configuration](docs/SPEC.md#configuration--phase-3) and
[schema 1.0](docs/SPEC.md#json-schema-version-10) for exact contracts.

`--json` retains console output and atomically replaces an existing report.
Its directory must exist. Input/configuration aliases are rejected, including
supported symbolic/hard links. Failed exports preserve existing reports and
clean up temporary files. **Reports retain usernames and raw log text.** See
[export safety](docs/SPEC.md#atomic-export-and-path-protection).

## Limits and delivery

Input is a narrow UTF-8 SSH password format requiring a year and timezone;
traditional syslog timestamps and public-key messages are skipped. Files are
analyzed offline and events/reports stay in memory. Large-log performance is
unverified. Shared IPs and missing logs limit interpretation. There is no live
monitoring, blocking, dashboard, database, or external intelligence lookup.
IDs are stable for the same source records/line numbers, not globally unique.
Atomic replacement does not coordinate concurrent filesystem changes or
guarantee directory-entry crash durability.

Completed analysis exits 0, including findings. Read/configuration/export
errors exit 1; argument errors exit 2. GitHub Actions runs unittest on Python
3.11 and 3.14 on Ubuntu and Windows; observed outcomes and platform skips are
recorded in [PLAN](docs/PLAN.md), not inferred from the workflow definition.

- [First-release notes — accepted, unpublished](docs/RELEASE_NOTES.md)
- [Portfolio description, contribution disclosure, and proposed résumé wording](docs/PORTFOLIO.md)

The owner defined requirements, design decisions, and phase acceptance.
Codex assisted with implementation, tests, documentation, and delivery checks.
