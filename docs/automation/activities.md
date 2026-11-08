# Week 13 activities

## Activity 1: Three contrasting office trigger decisions

| Controlled workflow | Requirement and chosen pattern | Alternative and trade-off | Ownership / adverse path |
|---|---|---|---|
| Attendance session overdue | Minutes-scale latency, schedule awareness; server-clock scan with deduplicated durable alerts | Event-only cannot discover a missing submission; aggressive polling adds load | Teacher submits; supervisor reviews escalation; unavailable worker detected by freshness |
| Validated office request received | Low latency per valid event; authenticated event plus transactional outbox | Scheduled export is simpler but delays each request; webhook authenticity/replay must be controlled | Request owner reviews permanent validation error; no blind retries |
| Daily aggregate office summary | Fixed cutoff and small batch; scheduled aggregation with explicit timezone and stable date/run identity | Recompute on every change offers freshness but adds work/partial-state confusion | Supervisor reviews late records; rerun is idempotent and labels cutoff |

The latter two are design exercises, not claims that additional office systems were implemented. All require trusted inputs, controlled data, finite retries, explicit authorization, and owned failure review. Volume, staffing, latency and privacy constraints justify different triggers rather than a single tool for every task.

## Activity 2: Controlled failure injection

Execute the project's controlled adapter and failure tests. Before each run state the expected result. Required cases: normal delivery; one transient failure followed by success; permanent rejection routed to human action; three failed attempts reaching exhaustion; duplicate scan/request; restart with pending retry. Preserve original outcomes and relevant regressions.

| Observation to establish | Evidence requirement |
|---|---|
| No duplicate processing | Stable event ID and unchanged logical attendance/alert count after repeated operation |
| No endless retries | Final attempt count at or below 3 and terminal/owned state |
| No silent data loss | Attendance remains persisted despite provider failure; pending/failed work remains visible |
| Safe recovery | Restart resumes persisted state; correlation/event history explains transition |

Observed execution: `evidence/week13/automation.json` records normal delivery after 1 attempt, transient recovery after 2, permanent rejection after 1 with action-required/escalation, and unavailable-provider exhaustion after 3 with action-required/escalation. Normal/transient each create exactly 1 controlled-event inbox entry; permanent/unavailable create 0. All four expected outcomes passed. The clock advanced by 100 seconds between scans; these are controlled-state results rather than measured wall-clock retry timings. Backend worker tests additionally verify missed-session deduplication without creating attendance/absence, bounded timeout, lease recovery and manual retry.

Interpretation: persisted stable identities and finite policy explain observed deduplication and bounded work. Recommendation: verify transport-specific idempotency/timeouts and ambiguous outcomes before adding an external provider. A passing local inbox exercise does not establish email/SMS delivery. Preserve the original actual transitions in the JSON and use the evidence index for full source/environment/time metadata.
