# ADR-001: Bounded web attendance architecture

Status: project design decision; instructor and stakeholder approval have not been supplied. Review when deployment scale or ownership changes.

Context: the course requires a Flutter Web client, an API integration, automation, safe failure handling, security verification, and reproducible evidence. The prototype runs with fictional data on a controlled host and one worker. Available time favors explicit components that can be explained during a viva.

Decision: Flutter Web + FastAPI + SQLite with migrations + one persistent worker. Keep authorization/business rules server-side and use an integration adapter for local notification delivery. Choose Python's standard SQLite interface to reduce the persistence abstraction a student must defend. Use separate modules and transactions to keep a later database migration possible.

Alternative: Flutter Web + FastAPI + PostgreSQL + managed queue/workers. It provides stronger concurrent-write and distributed processing options but adds server/service operation, deployment configuration, credentials, and failure modes. A frontend-only/local-storage application is rejected because it cannot establish trusted multi-role authorization or durable independent automation.

Scores below are reasoned design estimates from 1 (weak) to 5 (strong), not performance observations. Both feasible options pass the required-functional-fit gate. Equal security scores mean either requires the same controls; neither database inherently proves security.

| Criterion | Weight | SQLite + one worker A | PostgreSQL + queue B |
|---|---:|---:|---:|
| Implementation effort / available skills | .30 | 5 | 2 |
| Reliability options | .25 | 3 | 5 |
| Security controllability | .20 | 4 | 4 |
| Scale/concurrent writes | .10 | 2 | 5 |
| Cost / ownership simplicity | .15 | 5 | 2 |
| Weighted total | 1.00 | **4.00** | **3.45** |

Sensitivity: if scale matters more, weights `(effort .10, reliability .30, security .20, scale .30, ownership .10)` produce A **3.30**, B **4.20**. Recommendation reverses. Therefore A fits the bounded academic context, not an unmeasured production workload.

Consequences: SQLite may serialize writes and is not a shared database for multiple application hosts. One worker must be supervised and monitored. Migrations, consistent backups, TLS, secret rotation, and recovery still require operational ownership. Durable uniqueness and idempotency are needed even with one worker; a process restart must not erase reminders or retry state.

Evidence needed: actual API/UI tests, concurrency/conflict checks, restart recovery, workload measurements, TLS/security negatives, and restoration verification. No score substitutes for execution evidence. Review conditions: high contention, multiple hosts, external notification provider, stronger availability objectives, real personal records, or formally approved broader scope.
