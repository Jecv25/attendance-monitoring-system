# Controlled deployment, monitoring, and recovery runbook

Use the root README and executable scripts for exact commands and configuration names. This guide establishes the procedure and decision criteria; actual runs and recovery results must be linked through the evidence index.

## Release preparation

1. Record source/build, OS/runtime/tool versions and fictional dataset.
2. Review required tests, open defects, secret-free configuration example and migration changes.
3. Create separate controlled deployment configuration, database and protected keys. Do not use real personal records or production endpoints.
4. Back up the previous database consistently and retain the matching prior application/configuration reference. A copy taken during uncoordinated writes is not a verified consistent backup.
5. Apply supported migrations. Start API and exactly one worker using documented commands. Serve the Flutter release artifact through the controlled same-origin or explicitly configured API setup.
6. For HTTPS, configure a valid certificate/private key and client trust for the test CA if local. Do not disable certificate verification. Mark any untested TLS condition honestly.
7. Check liveness, readiness, worker freshness, due work, outbox state and the normal attendance path.

## Environment comparison

| Concern | Development | Controlled deployment | Required evidence |
|---|---|---|---|
| Data/config | Separate ignored local settings and fictional database | Separate deployment database/settings | Inspected resolved nonsecret settings |
| Transport | Explicit localhost HTTP exception may apply | HTTPS with verified trust and Secure cookie | Actual TLS verification; browser status separate |
| Client | Development/release as actually run | Built Flutter Web artifact | Build output and served workflow |
| Worker | Manually started single worker | Documented supervision/startup and heartbeat | Actual worker readiness/failure observation |
| Secrets | Local ignored values | Separately injected protected values | Redacted configuration/source scan |
| Database | Migrations and local constraints | Same supported schema/compatible upgrade | Version/integrity and workflow checks |

This is a comparison checklist, not an assertion that both environments were executed. Record each inspected/observed state explicitly.

## Owned monitoring map

| Signal | Interpretation | Action owner |
|---|---|---|
| Liveness | API process can answer a minimal request | Administrator restarts/investigates process |
| Readiness/database | API can access required persistent state | Administrator restores dependency/config; stop unsafe writes |
| Worker freshness | Scheduled monitoring is running recently enough | Administrator restarts worker; supervisor reviews overdue backlog |
| Pending/oldest outbox | Delivery work may be lagging | Administrator checks provider and worker |
| Failed/escalated notification | Automatic delivery ended or human action required | Supervisor acknowledges and follows up |
| Unsubmitted overdue session | Attendance remains pending, not student absence | Assigned teacher completes/reviews; supervisor handles escalation |

## Rollback/recovery rehearsal

Confine exercises to a dedicated controlled directory/database. Verify absolute paths before replacing files. Preserve evidence and the pre-exercise backup; do not delete unrelated project files.

1. State the failure and success criteria before the exercise.
2. Stop the exercise instance/worker or otherwise establish a consistent restoration boundary.
3. Create and verify a consistent SQLite backup using the supported backup operation; record schema and integrity result.
4. Introduce a safe controlled failure or restore a dedicated recovery copy. Do not corrupt the only demonstration database.
5. Restore compatible data and the matching application/configuration version. If schema rollback is unsafe, prefer a documented forward fix or full compatible backup restoration.
6. Restart API and worker; check readiness, database integrity, persisted session/attendance/audit values and retry state.
7. Rerun the main attendance workflow and relevant authorization/failure regression.
8. Record duration, commands, expected/actual results, remaining limits and the safe location of evidence.

Rollback triggers include failed migration, integrity failure, broken main path, unauthorized access, or sustained unacceptable errors. Communicate who owns the decision and what data may be lost between backup and incident. A successful database-copy test does not prove restoration of secrets, full machine state or an external service.
