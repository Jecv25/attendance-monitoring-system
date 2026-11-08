# Test strategy and Week 15 Activity 1

Exit criteria: required bounded workflow works from browser/API to database; adverse paths are explicit and safe; original failures and relevant regressions are preserved; no unsupported security/performance/UAT claim is treated as a pass. Use fictional deterministic fixtures and separate temporary databases. No production service or personal data is needed.

The [executed test catalog](test-catalog.md) maps actual final JUnit cases API-001–API-040 and actual Flutter cases UI-001–UI-011 to requirement families, expected outcomes and results. The original-failure/fix mappings are in [hardening record](hardening-record.md); browser and deployment checks remain separate artifacts in the root evidence index.

| Requirement / risk | Test family | Preconditions and controlled input | Unambiguous expected outcome |
|---|---|---|---|
| WEB-01 / normal path | API + Flutter + browser | Admin class/roster/session; assigned teacher | Save/finalize persists explicit statuses; report/audit agree |
| E validation | Invalid / boundary | Missing/oversized name, malformed ID/time, unknown status, out-of-roster student | Safe validation rejection, no partial mutation |
| E finalization | Functional / boundary | One Pending student, then complete roster | Incomplete finalization rejected; complete succeeds once |
| E correction | Authorization / audit | Finalized session; correct with and without reason | Ordinary edit rejected; authorized reasoned correction audited |
| E idempotency | Contract / reliability | Repeat same key/body, then same key/different body | Same operation result without duplicate; changed payload conflicts |
| E stale state | Concurrency | Two updates from same initial version | One applies; stale mutation conflicts without overwrite |
| W14 sessions | Authentication | Missing, altered, expired, then logged-out session | Protected data denied; expiration/logout invalidate access |
| W14 authorization | Function + object | Supervisor write; teacher accesses other class | Forbidden or safe inaccessible-resource response; no state change |
| W14 CSRF | Security | Authenticated write lacking valid CSRF | Rejected; ordinary valid write succeeds |
| W14 envelope | Security / interoperability | Valid, tampered, wrong-key, expired, replayed report | Fresh valid one accepted; every adverse case rejected safely |
| W13 outbox | Reliability | Local provider transient/permanent/exhaustion modes | Max3 total attempts; retry or human routing as classified |
| W13 restart | Recovery | Persisted pending notification, process restart | Work resumes with original attempt budget and event identity |
| W16 health | Reliability | Healthy then unavailable database/stale worker | Liveness/readiness semantics distinguish conditions |
| WEB-02–04 | Widget/state/accessibility | Loading/empty/validation/auth/conflict/network states at chosen widths | Readable operable feedback; recoverable errors retain unsaved entries |

API contract checks include resource/method/status/schema/version/serialization/pagination, duplicate/not-found/conflict behavior, and explicit error shape. These are executed through the project's test suite or equivalent collection, not screenshots alone. Browser checks establish integrated behavior where the environment permits; widget tests isolate state transitions and layouts.

Record exact test ID, command, source/build, environment, data, UTC execution time, expected/actual result, artifact and defect link. Safe logs correlate state transitions; they must not include authentication material. A passed test proves only the case and environment exercised. External delivery, distributed concurrency, production capacity and independent UAT remain separate questions.
