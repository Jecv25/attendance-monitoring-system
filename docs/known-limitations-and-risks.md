# Known limitations and residual risks

The project is a controlled academic prototype, not an authorized production attendance service. Verified results must be read with the actual environment/build/data scope in `../EVIDENCE_INDEX.md` and `../PROJECT_COMPLETION_REPORT.md`.

| Limitation / risk | Current boundary and realistic next action |
|---|---|
| Attendance is a human assertion | No biometric/geolocation/physical-presence proof. Teachers decide explicit statuses and corrections; Pending is never inferred Absent. |
| Single host and SQLite | One application host and one worker; writes can serialize. Evaluate PostgreSQL/managed queue and supervision before multi-host or heavier concurrent writes. |
| Local notifications | Demonstrates persisted inbox delivery/retries/escalation, not real email/SMS. An external adapter needs transport timeout, provider idempotency, credentials and delivery evidence. |
| Ambiguous provider timeout | Caller-side timeout does not cancel arbitrary underlying provider side effects. Supplied local inbox deduplicates event IDs; external transport needs its own safe policy. |
| Bounded data views | Report totals cover the displayed page (up to 100); dashboard is latest 100 accessible sessions. Do not interpret them as all-history institutional totals. |
| Date semantics | Stored UTC; displayed Asia/Manila. Report date filters are UTC calendar days and can differ from local-day expectations. |
| Roster snapshots | A session retains the roster captured at creation. Later roster edits do not silently alter it; administrative correction policy must be reviewed for real operation. |
| Local HTTP development | Explicit loopback development exception; deployment requires HTTPS/Secure cookies. Trusted API TLS and browser HTTPS trust are separate verification claims. |
| Local certificate lifecycle | Evaluation CA/certificates are local, restricted artifacts with short validity, not public hosting or system/browser trust configuration. |
| Secrets and endpoint compromise | Backend keys/sessions require protected host/config/backups. XSS, malware or a compromised authorized account can undermine endpoint trust despite transport/cryptography. |
| Database at rest | SQLite file is not encrypted by the application. Restrict filesystem/backups and evaluate storage encryption before real educational records. |
| Key lifecycle | One active report-key version; rotation may invalidate outstanding envelopes. Key loss cannot be repaired from committed source. |
| Retention | Expired auth/login/replay and old idempotency cleanup is implemented; no institution-approved attendance/audit purge policy is implied. Requests outside idempotency retention lose historical response guarantees. |
| Short performance evaluation | Two 20-second read-heavy local models, small seed, single runs. No endurance/stress/internet/distributed capacity or write-throughput claim. |
| Recovery scope | Actual isolated SQLite restoration and main-path verification; full host/infrastructure rollback remains a documented procedure unless separately evidenced. |
| Independent assurance | Developer tests/review do not constitute an independent penetration test, production approval, or stakeholder acceptance. |
| Accessibility/test breadth | Browser focus and responsive captures plus widget semantics/layout checks do not constitute a full screen-reader/WCAG audit. Forty backend cases and 86.465% statement coverage leave untested paths; no branch-coverage completeness is claimed. |
| Platform coverage | Executed Windows environment; Linux/macOS guidance is not evidence those platforms were tested. |
| Human assessment | Actual representative UAT/sign-off, peer-team review, timed student mock defense, viva/examination, contribution record and personal reflection remain pending real participants. |
| Dependency compatibility | Backend tests emit one TestClient/httpx deprecation warning. Review supported dependency migration during maintenance; do not hide the warning or equate it with a test failure. |

Prioritize unresolved correctness/access failures first, then operational protection, real participant evaluation, larger repeated workloads, external-provider assurance and architecture scale. Only an authorized owner can accept broader scope and residual risk.
