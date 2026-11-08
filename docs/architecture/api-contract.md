# API contract summary

The implemented API is version `1.0.0`; generated OpenAPI at `/api/openapi.json` and interactive docs at `/api/docs` are authoritative for exact schemas. Source anchors: `backend/app/main.py`, `schemas.py`, `domain.py`, `security.py`, `database.py`; migrations in `backend/migrations/`.

Authentication uses the HttpOnly `attendance_session` cookie. Authenticated writes require the current `X-CSRF-Token`. Attendance save/finalize/correction also require `Idempotency-Key` of 8–100 safe alphanumeric/underscore/hyphen characters. A repeated key with the same actor/scope/payload returns the stored result; a different payload conflicts. Obtain `csrf` from authorized login/current-session responses; keep it in memory, not published evidence.

| Method / path | Purpose and authority |
|---|---|
| `GET /api/health/live` | Minimal process signal |
| `GET /api/health/ready` | Database and worker freshness; 503 until a heartbeat is less than 45 seconds old |
| `POST /api/auth/login` | Establish session; generic invalid-credential response and bounded throttling |
| `GET /api/auth/me` / `POST /api/auth/logout` | Current identity / invalidate current session |
| `GET, POST /api/users`; `PUT /api/users/{id}`; `POST /api/users/{id}/password` | Admin user management/reset |
| `GET, POST /api/students`; `PUT /api/students/{id}` | Authorized read; Admin management |
| `GET, POST /api/classes`; `PUT /api/classes/{id}` | Scoped class read; Admin creation/assignment |
| `GET, PUT /api/classes/{id}/roster` | Scoped read; Admin roster management |
| `GET, POST /api/sessions`; `GET /api/sessions/{id}` | Scoped read; Admin scheduling and snapshot roster |
| `PUT /api/sessions/{id}/attendance` | Admin/assigned Teacher; version + unique student/status items |
| `POST /api/sessions/{id}/finalize` | Authorized writer; version; all explicitly marked |
| `POST /api/sessions/{id}/corrections` | Authorized writer; version, student, status, 8–240-character reason |
| `GET /api/reports` / `GET /api/dashboard` | Role/class-scoped summaries |
| `GET /api/alerts`; `POST /api/alerts/{id}/retry` | Scoped alerts; authorized writer requeues only action-required work |
| `GET /api/audit` / `GET /api/metrics` | Permitted audit; oversight-only operational metrics |
| `POST /api/reports/exchange/send`, `/receive` | Admin-only authenticated-encryption exercise |

JSON attendance-save example (fictional IDs; no authentication material):

```json
{"version": 0, "items": [{"student_id": 1, "status": "present"}, {"student_id": 2, "status": "late"}]}
```

Successful save returns a confirmation and incremented version. Use that version for the next action. Preserve the exact original request and idempotency key for a safe retry after an uncertain outcome. A conflict requires reconciliation rather than generating a new key and overwriting blindly.

Common responses: `200` successful operation/read, `201` resource creation, `401` missing/invalid/expired session, `403` role/class/CSRF/Origin rejection, `404` missing resource, `409` duplicate/stale/idempotency/replay conflict, `413` oversized body, `422` invalid fields/business rule or unverifiable report, `429` login throttle, `503` required dependency/configuration unavailable, safe `500` unexpected failure. Generated OpenAPI and actual tests establish endpoint-specific behavior.

Limits: paged lists allow 1–100 items with nonnegative offset; rosters and attendance batches are bounded at 100; attendance input forbids duplicate students; schedule duration is greater than zero and at most 24 hours with explicit timezone; paired report dates must be ordered and at most 366 days apart. Report filters are **UTC calendar days**, even though interface timestamps display Asia/Manila. Report totals cover the **displayed page**; dashboard scope is the **latest 100 sessions**. These bounds must remain visible, not misrepresented as all-history totals.

Manual alert recovery creates a separate stable recovery event with its own finite attempt budget; it does not reset history or rerun attendance writes. Repeated recovery of the same original event deduplicates. Operational notes should explain why recovery was requested; the current retry endpoint has no free-text reason payload.
