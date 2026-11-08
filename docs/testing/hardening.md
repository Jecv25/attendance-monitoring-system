# Hardening backlog and Week 15 Activity 2

This document separates the intentionally weak **exercise fixture** from real implementation findings. Do not introduce weak settings into the application to produce artificial historical failures.

## Isolated weak-configuration review

The following is a non-executable classroom scenario, not active configuration:

| Weak proposal | Likelihood / impact | Priority | Corrected direction |
|---|---|---|---|
| Trust a role supplied by the browser | High / high: privilege escalation | P1 | Load trusted account role and object authorization server-side |
| Hardcode encryption key in Flutter | High / high: public secret | P1 | Backend-only protected secret injection |
| Log every request including passwords/cookies | High / high: credential disclosure | P1 | Structured allowlisted event metadata and redaction |
| Disable TLS verification | Medium / high: wrong service trusted | P1 | Trusted CA and hostname validation |
| Retry forever after any error | High / medium: unbounded processing | P2 | Classified failures, timeouts and max3 attempts |
| No backup verification | Medium / high: unrecoverable loss | P2 | Consistent backup + actual restoration/integrity/workflow checks |

Prepared improvement plan: implement P1 controls first, then finite reliability/recovery, run original negative cases and relevant normal regressions, retain before/after exercise review. This table verifies reasoning only. Runtime control results require actual source/test evidence.

## Genuine defect record

Actual preserved failures, three fixes, original-case reruns and regression results are recorded in [the detailed hardening record](hardening-record.md). These were genuine implementation findings; no vulnerabilities were planted to manufacture before/after results.

| ID | Actual observation + evidence | Risk / priority | Actual fix | Original-case rerun | Relevant regression | Status |
|---|---|---|---|---|---|---|
| HARD-01 | Dashboard/report-exchange500 from direct route defaults | P1 | Pure report helper with concrete defaults | Original dashboard/exchange cases pass | Final40-test backend suite | Verified |
| HARD-02 | Rejected Origin/oversized-body responses bypassed headers/correlation | P1 | Common response decoration/logging | Original403/413 cases pass | Final40-test backend suite | Verified |
| HARD-03 | Normalized password incorrectly accepted | P1 | Preserve password semantics in creation/reset/login | Original normalized-alternative case rejects401 | Final40-test backend suite | Verified |

Prioritize by likelihood, impact and exposure. Review validation, role/class access, cookie/CSRF settings, rate controls, safe errors, dependency versions, logging, request limits, idempotency, transactions, and recovery. A defect record needs reproducible steps; a source-review hardening improvement must be labeled as such instead of claiming a previously failed runtime test.
