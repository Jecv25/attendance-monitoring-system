# Conceptual data model

This is the conceptual model. Migrations and the generated OpenAPI contract are authoritative for exact column and field names. Update this file if implementation changes the relationships.

```mermaid
erDiagram
  USER ||--o{ CLASS : teaches
  CLASS ||--o{ ROSTER : contains
  STUDENT ||--o{ ROSTER : joins
  CLASS ||--o{ ATTENDANCE_SESSION : schedules
  ATTENDANCE_SESSION ||--o{ ATTENDANCE : records
  STUDENT ||--o{ ATTENDANCE : receives
  USER ||--o{ AUTH_SESSION : authenticates
  USER ||--o{ AUDIT : performs
  ATTENDANCE_SESSION ||--o{ OUTBOX : generates
  USER ||--o{ IDEMPOTENCY : submits
```

Attendance uniqueness is `(session, student)`, with authoritative membership checks. `session_students` snapshots the roster at session creation; later class-roster edits do not silently change that session's attendance obligation. `sessions.version` is the optimistic update precondition. Finalization requires every snapshot-roster entry to be explicitly marked. An authorized correction retains actor, reason, and old/new attendance information appropriate to the minimized audit record.

Persist authentication expiration/invalidation, idempotency request fingerprints and results, stable outbox event identities and attempts, delivery state, worker freshness, and accepted encrypted-message identities. Use UTC timestamps in storage; convert to Asia/Manila at the interface boundary. Transaction boundaries must include the associated state and audit/idempotency changes.

Foreign keys, uniqueness, bounded fields, and domain checks support rather than replace authorization and business-rule validation. Runtime databases and consistent backup files are local artifacts, not source deliverables.

Implementation anchors: `backend/migrations/001_initial.sql` defines `users`, `auth_sessions`, `login_attempts`, `students`, `classes`, `rosters`, `sessions`, `session_students`, `attendance`, `idempotency`, `audit`, `notifications`, `inbox`, `replays`, and `worker_health`. `backend/app/database.py` applies numbered migrations, enables foreign keys/WAL, and uses `BEGIN IMMEDIATE` for write transactions. This is source inspection, not evidence that all runtime cases passed.
