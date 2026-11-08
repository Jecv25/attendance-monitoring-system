# Project completion report

Delivery date: 8 November 2026, Asia/Manila. Project: **Attendance Monitoring System / Presence**. Academic source: supplied PFEBSIT 002 Flutter Web student module. No instructor approval or institutional acceptance is claimed.

## Implemented result

Flutter Web is connected to FastAPI and a persistent, migrated SQLite database. Admin manages users, students, classes, assignments, rosters and sessions. Teachers save/finalize assigned attendance and make reasoned corrections. Supervisors have read-only oversight. Session rosters are snapshots; database constraints, transactions, optimistic versions and idempotency protect attendance writes.

A separate durable worker detects pending/overdue sessions, delivers local notifications with timeout/backoff/max-three attempts, escalates permanent/exhausted failures and recovers persistent work. Authentication uses Argon2id, hashed opaque sessions, HttpOnly cookies and CSRF; backend role/object checks are authoritative. Report exchange uses AES-256-GCM, authenticated metadata, expiry and persistent replay protection.

## Verified results

| Check | Actual result |
|---|---|
| Backend/API suite | 40 passed, one test-client deprecation warning; 86.465% statement coverage |
| Flutter state/layout suite | 11 passed; desktop1440, tablet768 and narrow390 widths included |
| Flutter analysis and release | No issues; release web builds succeeded; final metadata-cleanup build30.8s |
| Browser workflow | Eight checks passed; no application page errors; screenshots retained |
| Automation exercises | Normal1attempt, recovered transient2, permanent1 routed for action, unavailable3 exhausted; deduplication verified |
| Security | Invalid/expired/altered sessions, CSRF, role/object access, tampering, wrong key, expiry and replay covered |
| Local HTTPS | Explicit trusted CA succeeds, untrusted certificate rejected, secure cookie/HSTS and protected exchange verified |
| Ordinary workload | 276 requests; p95 22.581ms; no unexpected errors |
| Peak workload | 3062 requests; p95 44.702ms; no unexpected errors |
| SQLite recovery | Consistent backup restored12students, integrityok, attendance save/finalize200 |
| Actual worker restart | PIDchanged, heartbeatadvanced, persisted interrupted-lease event delivered on attempt2 |
| Operator commands | `scripts/run.ps1 -SkipBuild` started app/worker, readinesstrue; `scripts/stop.ps1` stopped owned processes |

The original backend, password, Flutter and strict-certificate failures are retained with subsequent fixes. Original browser harness failures are distinguished from backend authentication failures. Credentials in original synthetic test failure output were redacted before publication.

## Weekly completion

| Week | Technical and portfolio status | Human assessment boundary |
|---|---|---|
| 13 / SA7 | Implementation, trigger comparisons, controlled failures, logs, recovery policy and maintainability artifacts completed and technically verified within documented scope | Student explanation/assessment acceptance not inferred |
| 14 / SA8 / IA5 | Access controls, cryptographic exercise, negative cases, strict TLS, security activities and residual-risk records completed | Student defense/assessment acceptance not inferred |
| 15 / IA6 | Traceable tests, three genuine hardening fixes, original failures and passing regressions completed | Instructor grading external |
| 16 | Measured ordinary/peak reads, resource samples, health/profile comparison, restoration/restart and conditional recommendation completed | Independent infrastructure/stress/endurance not demonstrated |
| 17 / SA9 / AS3 | OpenAPI, architecture alternatives/scoring/sensitivity, repository guidance, maintenance and complete UAT package prepared | Actual representative-user UAT, dispositions/retests and sign-off Pending Human Participation |
| 18 / E3 | Executed developer browser walkthrough, fallback evidence, internal review, timed scripts and viva/reflection templates prepared | Actual peer-team review, timed student mock defense, panel demonstration, viva/examination and personal reflection Pending Human Participation |

The academic project is not represented as fully accepted while these human activities remain pending. [Traceability](REQUIREMENTS_TRACEABILITY.md) and [evidence index](EVIDENCE_INDEX.md) provide the detailed map.

## Run and handover

From a checkout with Flutter installed: `scripts/setup.ps1`, then `scripts/run.ps1`. Open `http://127.0.0.1:8000`. Usernames are admin/teacher/supervisor; setup generates passwords in the ignored local `.env`. See [README](README.md) for individual processes, dev server, test commands and [deployment](deployment/README.md) for explicit-CA HTTPS.

Readiness recommendation: suitable for a controlled local academic demonstration, conditional on preflight checks and the fictional dataset. It is not a production approval. SQLite/single-worker topology, same-host measurements, local-only message delivery, lack of database-at-rest encryption and pending independent UAT remain material limitations. See [risks](docs/known-limitations-and-risks.md) and [maintenance](docs/maintenance.md).

Remaining human actions: run the representative UAT with real volunteers using fictional data; record genuine findings and approved retests; obtain authorized acceptance; perform peer-team review and timed mock defense; complete each student's own contribution/reflection; undertake the actual viva and examination. No names, signatures or results are invented.
