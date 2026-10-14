# Phase 1 fixture expectations

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
