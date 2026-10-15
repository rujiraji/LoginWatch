# Proposed first-release notes

Status: Phase 4 Implemented — awaiting review. This is a proposed release
description, not a published release or final acceptance. No tag has been
created. The owner decides whether to accept and release the project.

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

Phase 4 fresh-checkout and CI results will be recorded in [PLAN.md](PLAN.md)
after execution. A workflow definition alone does not establish compatibility
or a passing check. CI uses hosted Python installations and performs no
application package install.

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
