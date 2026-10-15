# Synthetic fixture expectations

## Original parsing sample

`sample.log` is entirely synthetic. Its 15 lines have these independently
specified outcomes:

| Lines | Expected outcome |
| --- | --- |
| 1, 2, 5, 6, 9 | Five failures; line 2 extracts `admin` from `invalid user admin` |
| 3, 4, 7, 8 | Four successes |
| 10, 11 | Two ignored blank lines, including a whitespace-only line |
| 12 | Skipped unsupported text |
| 13 | Skipped invalid IPv4 address |
| 14 | Skipped port zero |
| 15 | Skipped public-key authentication |

Expected totals: **9 parsed events, 4 successes, 5 failures, 3 unique IPs,
5 unique usernames, 2 ignored blank lines, and 4 skipped nonblank lines**.

The unique IPs are `192.0.2.10`, `198.51.100.20`, and `2001:db8::1`.
Lines 6 and 7 use equivalent IPv6 spellings. Usernames are `alice`, `admin`,
`bob`, `carol`, and `Alice`; case matters. Skipped records contribute no IPs
or usernames. Lines 1 and 9 are identical but remain two observations.
Lines 3 and 8 denote the same UTC timestamp, `2026-10-11T15:02:00Z`, and
line 9 is out of timestamp order; Phase 1 retains source order.

Phase 2 adds **zero findings** for this fixture: no IP has five failures in
300 seconds or failures against five usernames in 600 seconds, and no success
follows five same-IP/account failures. The original summary is unchanged.

## Normal activity demo

`normal.log` has 8 events: 6 successes, 2 failures, 3 unique IPs, 3 unique
usernames, no blank or skipped lines, and **zero findings**. Lines 2 and 5
are isolated failures on different IPs/accounts; subsequent successes remain
below the same-account threshold. All other lines are successful logins.

Run: `python loginwatch.py samples/normal.log`.

## Suspicious activity demo

`suspicious.log` has 14 events: 3 successes (lines 6–8), 11 failures,
3 unique IPs, 7 unique usernames, no blank or skipped lines, and **five
findings**, in the order below. These expectations are specified from the
fixture's timestamps and source lines independently of analyzer output.

| Rule | IP | Trigger (UTC) / source line | Supporting lines | Reason |
| --- | --- | --- | --- | --- |
| repeated_failures | 192.0.2.10 | 10:05:00 / 5 | 1, 2, 3, 4, 5 | Five failures within 300 seconds; the earliest is exactly on the boundary |
| success_after_failures | 192.0.2.10 | 10:05:01 / 6 | 1, 2, 3, 4, 5, 6 | Success after five failures for alice on this IP within 600 seconds |
| success_after_failures | 192.0.2.10 | 10:05:02 / 7 | 1, 2, 3, 4, 5, 7 | Another qualifying success; line 6 is not failure evidence |
| multiple_accounts | 198.51.100.20 | 10:30:00 / 13 | 9, 10, 11, 12, 13 | Failures for admin, guest, root, service, backup within 600 seconds |
| multiple_accounts | 198.51.100.20 | 10:30:01 / 14 | 10, 11, 12, 13, 14 | Line 9 expires during the gap, ending the prior episode; the new admin failure restores five distinct usernames |

All dates are 2026-10-11. Finding IDs are `<rule>:<IP>:line-<trigger line>`.
Repeated-failure evidence contains 5 events; each success finding contains
6 events including its triggering success; each multiple-account finding
contains 5 failures. The first three findings involve only `alice`; the last
two involve the same five usernames listed above, stored in alphabetical order.

Line 8 is deliberately out of timestamp order and unrelated to the triggering
IP/account. It contributes to the summary but to no finding. The later IP's
failures are spread far enough apart that it never reaches five failures in
300 seconds. The five different accounts cannot satisfy same-account success
correlation. Console explanations identify the threshold, UTC trigger and
evidence range, and every supporting source line.

Run: `python loginwatch.py samples/suspicious.log`.

## Custom-threshold demo (Phase 3)

`custom.log` contains five synthetic events: four failures (lines 1, 2, 4, 5),
one success (line 3), two IPs, three usernames, and no blank/skipped lines.
With defaults it has **zero findings**. The two failures on each IP are below
all default count thresholds.

`custom-config.json` sets all three counts to 2, with windows of 30 seconds
for repeated failures and 60 seconds for the other two rules. With this
configuration exactly **three findings** are expected, in this order:

| Rule | IP | UTC trigger / source line | Evidence lines | Actual count/window threshold |
| --- | --- | --- | --- | --- |
| repeated_failures | 192.0.2.10 | 10:00:30 / 2 | 1, 2 | 2 failures / 30 seconds |
| success_after_failures | 192.0.2.10 | 10:01:00 / 3 | 1, 2, 3 | 2 failures / preceding 60 seconds |
| multiple_accounts | 198.51.100.20 | 10:11:00 / 5 | 4, 5 | 2 distinct usernames / 60 seconds |

All dates are 2026-10-11. Each first observation is exactly on the relevant
window boundary. The later IP's failures are 60 seconds apart, so its
30-second repeated-failure rule stays quiet. Only one username appears in the
earlier IP's failures, so its multiple-account rule stays quiet. The successful
event is included in success-after-failures evidence but not its threshold
failure count. These expectations are specified from the fixture, not produced
by the analyzer.

Run from the repository root:

```bash
python loginwatch.py samples/custom.log
python loginwatch.py samples/custom.log --config samples/custom-config.json --json custom-report.json
```

The second command retains the console report and atomically replaces
`custom-report.json` on success. Its schema 1.0 report has `source_filename`
`custom.log`, all seven summary counts above, all six effective configuration
values from the file, and the three complete ordered findings/evidence sets
in the table. Repeating the command produces identical UTF-8 bytes. Generated
demo reports are ignored by Git; reports retain usernames and raw log text.
