# Portfolio description and proposed résumé wording

## Project description

LoginWatch is a Python CLI for reviewing a documented SSH password-login
format. It summarizes activity and reports three explainable patterns:
repeated failures, a success after same-account failures, and failures across
multiple accounts. Reports include source evidence, configurable thresholds,
and reproducible JSON with atomic file replacement. It runs offline using
the standard library and synthetic fixtures.

## Contribution disclosure

The project owner defined requirements, scope, architecture constraints,
detection and episode semantics, verification expectations, and phase
acceptance. The owner directed the work, supplied independent review results,
and merged accepted phases.

Codex implemented runtime code, tests, fixtures, documentation, and delivery
automation under those instructions. Codex also ran the checks recorded in
PLAN. Independent reviewer results supplied by the owner are labeled
separately from Codex's own checks. Do not describe the implementation as
entirely handwritten by the owner or claim the owner personally ran checks
that were supplied by an independent reviewer.

## Proposed résumé bullet

> Defined requirements and detection semantics for LoginWatch, a Python SSH-log
> analysis CLI with evidence-backed findings and reproducible JSON reports;
> directed AI-assisted implementation through phased independent review.

For a project page, the description can add:

> Specified inclusive time windows, duplicate-alert suppression, configuration
> validation, and atomic export safeguards, with synthetic fixtures and a
> repeatable demo documenting expected results and limitations.

These are proposed statements for owner review. They claim no deployment,
user adoption, incident prevention, throughput, time savings, or performance
improvement. Test and CI outcomes belong in the verification record; they
are not business-impact metrics. Phase 4 delivery remains awaiting review.
