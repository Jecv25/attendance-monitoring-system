# Maintenance and operational ownership

This is a proposed support plan for the controlled prototype. Named personnel and institutional approval have not been supplied; responsibilities are expressed by role.

| Cadence / trigger | Task | Owner and evidence |
|---|---|---|
| Each demonstration/startup | Health/readiness, worker freshness, fictional data/config, clock/timezone | Administrator; preflight record |
| Each teaching session | Review pending statuses, save confirmation, finalize explicitly | Assigned Teacher; attendance and audit |
| Daily while operating | Review overdue/failed/escalated work and follow-up | Supervisor; alert disposition |
| Before schema/release change | Review migrations/compatibility, backup, run normal and relevant negative regressions | Administrator/developer; release evidence |
| Weekly or before assessment | Consistent backup and integrity review; inspect protected storage/retention | Administrator; sanitized backup metadata |
| Monthly or after material change | Dedicated restoration rehearsal, dependency/security advisory review, docs consistency | Administrator/developer; actual restore/test results |
| Suspected compromise | Invalidate sessions/credentials as appropriate, rotate protected keys, inspect safe audit and retest | Authorized administrator; incident record without secrets |
| Scope/scale change | Re-evaluate SQLite, worker supervision, external provider, identity and real-data privacy | Project owner + supervisor; revised ADR and approval |

Do not schedule destructive retention without an approved policy. Expired auth/idempotency/replay records must retain enough history for their safety windows. Protect backups with at least the same access restrictions as the database. Key loss and backup freshness affect recovery; document them in each exercise.

Change control: record problem, affected requirements, decision/alternative, migration/security impact, tests, evidence, rollback condition, and owner. Keep APIs/versioned contracts and documentation aligned. Small domain modules, deterministic controlled tests, stable error shapes, migrations, adapter isolation and correlation IDs reduce maintenance effort but do not eliminate operational work.

Known limits to carry forward: no physical-presence proof, no production identity federation, local rather than email/SMS delivery, single-host/database availability, SQLite write constraints, unmeasured larger workloads, no independent penetration test, and pending genuine UAT/peer/exam/reflections. Report totals are page-scoped (up to 100 sessions), dashboard summarizes the latest 100, and report date filters use UTC days while displayed timestamps use Asia/Manila. Sessions snapshot rosters at creation. Update this list against actual implementation and verification rather than assuming every limitation is resolved.
