# Automation design, trigger contract, and recovery policy

Design baseline for M13 topics 1–5. Observed results belong in the evidence index; local notifications must not be described as delivered email or SMS.

| Pattern | Fit | Disadvantage / failure consideration |
|---|---|---|
| Browser timer | Immediate UI feedback | Stops with browser; rejected for monitoring |
| Backend polling/scheduled scan | Finds due and overdue sessions, recovers missed scans | Scan interval adds latency; worker ownership and trusted clock needed |
| Webhook/event only | Fast response to saved attendance | Cannot alone discover a session that was never submitted |
| Durable queue/outbox | Persists delivery intent and retry state | Requires claims, deduplication, and backlog monitoring |
| Hybrid scan + transactional state | Selected for bounded prototype | Single worker and database require supervision |

Trigger contract: the server-clock-driven worker scans persisted sessions for configured upcoming/pending/overdue thresholds. Create stable event identities per session, alert type, and recipient. Repeated scans must not create repeated logical alerts. Session completion/finalization is read from the authoritative database. Pending is not Absent.

Save attendance and its audit/idempotency result atomically. If a notification is caused by a transaction, persist its delivery intent without making attendance success depend on provider availability. Monitor work independently of browser state. Bounded batches and retry limits prevent one failing event from monopolizing processing.

| Failure class | Examples | Response / owner |
|---|---|---|
| Invalid/business-rule | Unknown roster student, unsupported status, incomplete finalization | Reject safely; teacher/admin corrects input; no blind retry |
| Authentication/authorization | Expired login, wrong role or class | Reauthenticate or deny; no privilege retry |
| Transient provider | Timeout, controlled temporary unavailability | Retry notification only, maximum 3 total attempts |
| Permanent provider | Invalid destination or explicit permanent rejection | Stop automatic delivery and route human action |
| Exhausted transient | Third unsuccessful attempt | Mark failed/escalated with actionable reason |
| Stale update | Session changed after UI loaded | Conflict; user reconciles |
| Worker restart | Process interruption before next attempt | Resume persisted due state; do not reset attempt budget |
| Database unavailable | Cannot establish authoritative state | Fail readiness and stop unsafe writes; administrator recovers |

Retry schedule: the source currently bounds provider waiting at 2 seconds; retries use `min(60, 2**attempt)` seconds plus random jitter from 0 to .25 seconds, with at most three attempts in total. The worker loops every 5 seconds, claims batches of at most 100 and leases claimed work for 30 seconds. Source defaults remind from 15 minutes before start until end, mark overdue 10 minutes after end, and escalate an unsubmitted session 30 minutes after the overdue threshold. A recent heartbeat is less than 45 seconds old. Verify actual timing in controlled tests rather than interpreting these settings as measured execution.

No retry is infinite; permanent errors bypass further automatic attempts. Stable provider/event identity must prevent duplicate side effects. A caller-side thread timeout does not cancel an arbitrary provider's underlying side effect, so a future external adapter must enforce transport timeouts/idempotency and handle ambiguous outcomes; the supplied local inbox deduplicates stable event identities. A circuit breaker is a possible later improvement for an external high-volume provider; it is not a replacement for the finite per-event retry budget. Failed/escalated outbox state serves the bounded dead-letter function.

Human recovery: inspect the safe alert, identify session/owner and failure category, correct the cause, then use only the documented authorized recovery operation. The retry endpoint audits the actor and creates a separate stable recovery event; explain the operational reason in the incident/UAT notes because the current retry API has no free-text reason field. Repeated recovery must not duplicate attendance or erase prior attempts/audit. Supervisors are read-only and review/escalate follow-up; an authorized Admin or assigned Teacher performs the retry. Never infer student absences to clear an alert.

Monitor worker freshness, oldest pending work, queue counts, attempts, failed/escalated events, and due sessions. Administrator owns process/database health; teachers own submitting assigned sessions; supervisors own escalation review. Logs use correlation/event IDs and state changes without request bodies or secrets.
