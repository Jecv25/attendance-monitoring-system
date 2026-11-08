# Architecture/security defense and viva preparation

These are study prompts and implementation-grounded explanation guides. A student must trace actual source and evidence independently; this file is not a record that an oral examination occurred.

| Question | Defensible explanation / evidence to inspect |
|---|---|
| Why Flutter Web? | Module-required browser client; reusable widgets/state/API patterns; mobile packaging is not required |
| Why keep API validation when forms validate? | Browser is untrusted; server establishes membership/role/state/limits before persistence |
| Why FastAPI/SQLite/one worker? | Bounded implementation and observable local persistence; ADR weighs alternative and admits serialized-write/single-host limits |
| Why both role and class checks? | A Teacher role alone does not grant every class; tampered IDs must not expand access |
| Why not automatically mark absence on overdue sessions? | Missing submission or dependency failure is not evidence of student absence |
| What makes a retry safe? | Stable identity, persistent idempotency/result, uniqueness/transactions, unchanged payload; provider retries do not repeat attendance writes |
| What happens after the third failure? | Finite attempt budget reaches visible terminal/escalated state with human ownership |
| How does restart recovery work? | Persisted outbox/attempt/due state; restart resumes rather than resetting budget or losing work |
| How are concurrent teacher updates handled? | Version/precondition conflict prevents silent overwrite; user reconciles |
| Hashing vs encryption? | Argon2 verifies passwords without reversible recovery; AES-GCM confidentially authenticates a report; HTTPS protects transit |
| Does encryption prevent replay? | No. Authenticated metadata, expiry and persisted accepted-message identity provide separate replay control |
| Why no keys in Flutter? | Compiled browser assets are public; secrets must remain in protected backend configuration |
| Liveness vs readiness? | Process answering is distinct from required persistent/worker dependencies being usable |
| What do workload results prove? | Only stated dataset/mix/concurrency/duration/environment; not endurance or production capacity |
| How do you know backup works? | Consistent backup, restoration/integrity check and main-path retest; existence alone insufficient |
| What remains unverified? | Read final completion report; separate human UAT/viva from developer verification and external delivery from local adapter |

## Timed mock defense — Activity 2

Each student: 1 minute explain an architecture trade-off; 90 seconds diagnose a controlled failure; 90 seconds interpret one real test/log/measurement artifact; 1 minute identify a residual risk and verification step. Record actual timing, participant, questions, responses/uncertainty, evidence used and follow-up. **Pending Human Participation** until performed.

Diagnosis exercise: notification retry remains pending after restart. Check worker freshness, persisted next-attempt time/attempt count, provider classification, ownership/claim state and safe correlated logs. Do not reset records blindly or rerun attendance writes. State uncertainty and the next observation needed.
