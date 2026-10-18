# First-release notes — accepted, unpublished

Status: **Accepted and release-ready, unpublished**. All four planned phases
are complete. The owner accepted Phase 4 following independent review of
commit `5df114e2da0ce37590e840822122e2d3a07aeb30`, PR #4. The PR awaits the
owner's final merge. No tag or GitHub release has been published.

## Delivered behavior

- Offline Python 3.11+ CLI with no third-party runtime dependencies.
- A documented UTF-8 SSH password-login format, IPv4/IPv6 validation, UTC normalization, retained source lines/raw text, and separate blank/skipped counts.
- Activity summaries and three explainable rules: repeated failures, success after same-IP/account failures, and failures across multiple accounts.
- Inclusive windows, deterministic ordering, failure-episode suppression/rearming, independent qualifying successes, and frozen evidence snapshots.
- Validated optional JSON configuration for all six thresholds, with immutable effective values and explicit positive 32-bit bounds.
- Console reports and schema 1.0 JSON with full findings/evidence, reproducible bytes, atomic replacement, alias protection, and concise error statuses.
- A walkthrough, component/interview notes, contribution disclosure, proposed résumé wording, and a standard-library demo verification script.
- GitHub Actions unittest matrix for Python 3.11/3.14 on Ubuntu/Windows.

This phase changes delivery documentation and verification tooling; runtime
behavior remains the accepted Phase 3 implementation.

## Verification status

Owner-reported independent Phase 3 review: Linux, Python 3.12.14, all 138
tests passed without skips, including symlink and hard-link protection. Demo
commands, JSON summaries/rules/thresholds/evidence, repeatable bytes, source
preservation, and temporary-file cleanup passed. This review applies to commit
`16751333a60bec6f93ec6568a46ecefb08d63966` and is distinct from Phase 4 checks.

Phase 4 verification by Codex on 2026-10-15: a clean GitHub clone at
`76b5f3bc1f38e4094de75b5fe6d00f8230e82061`, Windows/Python 3.14.6, using a new
virtual environment created without pip. No installed distributions were
present. Unittest reported `Ran 138 tests; OK (skipped=6)`; local symlink
creation is unavailable. All seven demo/help commands, full JSON/evidence
checks, repeat-byte comparisons, source preservation, and temporary cleanup
passed. The two literal documented export commands passed as well.

[CI run 38804423752](https://github.com/rujiraji/LoginWatch/actions/runs/38804423752)
for PR #4 passed all four jobs, each with 138 tests and **no skips**:

| Hosted platform | Verified Python versions |
| --- | --- |
| Ubuntu | 3.11.17 and 3.14.8 |
| Windows | 3.11.9 and 3.14.8 |

CI includes successful symlink/hard-link protection checks, uses hosted Python
installations, and performs no application package install. Python 3.11 is now
verified by these runs; it was unverified at earlier phase boundaries. CI runs
unittest; the separate fresh-checkout demo verification was local on Windows.
The run is associated with branch head `76b5f3bc1f38e4094de75b5fe6d00f8230e82061`;
the reviewed final implementation commit is covered separately below.

### Reviewed final-commit CI evidence

[CI run 38804749008](https://github.com/rujiraji/LoginWatch/actions/runs/38804749008)
for reviewed commit `5df114e2da0ce37590e840822122e2d3a07aeb30` passed all four
jobs: Ubuntu/Python 3.11.17 and 3.14.8, Windows/Python 3.11.9 and 3.14.8.
Each job ran **138 tests with no skips**. Codex rechecked the job results and
logs during acceptance finalization on 2026-10-17. PR #4 displays CI for any
subsequent acceptance-documentation commit.

### Independent Phase 4 review reported by the owner

These results are separate from checks run by Codex. The reviewer used Linux,
Python 3.12.14, and a new environment without pip or installed distributions:
all 138 tests passed without skips. The demo verifier and both literal export
commands passed. The reviewer independently confirmed all four final-commit
CI jobs (138 tests, no skips, Python 3.11/3.14 on Ubuntu/Windows), unchanged
runtime code/existing tests/fixtures, documentation, and relative file links.
No blocking issues were found. The reviewed commit was
`5df114e2da0ce37590e840822122e2d3a07aeb30`, PR #4.

### Codex acceptance-finalization checks

On 2026-10-17, Windows/Python 3.14.6: `python -m unittest discover -s tests`
reported `Ran 138 tests; OK (skipped=6)`, exit 0, due to local symlink creation
privileges. `python scripts/verify_demo.py` and the documented parsing sample
command passed; the verifier checked all seven demo/help commands, full JSON
evidence, identical repeat bytes, source preservation, and temporary export
cleanup. `git diff --check` passed. Only documentation changed after the
reviewed commit. Detailed commands and evidence are in [PLAN.md](PLAN.md).

## Known limits

Input support is deliberately narrow; traditional syslog timestamps and
public-key authentication are skipped. Analysis is offline and heuristic,
with no monitoring, blocking, external intelligence, dashboard, or database.
Shared IPs and missing logs limit interpretation. Events, evidence, and JSON
remain in memory; large-log performance is unverified. IDs depend on source
records and line numbers, not global identity. Reports retain usernames and
raw log text. Atomic export does not coordinate concurrent filesystem changes
or guarantee directory-entry crash durability. Some failure modes are
mock-tested; symlink tests skip on hosts that cannot create symlinks.

See [WALKTHROUGH.md](WALKTHROUGH.md) for the demo and
[PORTFOLIO.md](PORTFOLIO.md) for the owner/AI contribution split.
