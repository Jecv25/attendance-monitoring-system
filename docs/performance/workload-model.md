# Pre-measurement workload models — Week 16 Activity 1

Prepared before workload execution, then reconciled with the executed manifest. These are controlled models, not instructor-approved service objectives. The earlier written design suggested 1000/1500 ms p95 candidates; the executable script predefined the stricter 750 ms threshold for both runs. The final criteria below match that actual script/manifest rather than being chosen from the observed results. Raw observations and interpretation are in `results.md` and `../../evidence/week16/performance.json`.

| Parameter | Ordinary classroom use | Peak submission/review period |
|---|---|---|
| Fictional seed | Default demonstration seed: 1 class, 1 assigned teacher, 12 roster students, 1 current session; any additional workload fixture counts must be recorded before the run | Same dataset for comparability; state exact actual counts in manifest |
| Concurrent simulated users | 3 | 12 |
| Request mix | 50% dashboard/session lists, 30% authorized reports, 20% session detail | Same mix to isolate concurrency effect |
| Think time | 0.20 seconds per journey | 0.05 seconds per journey |
| Warm-up | 3 seconds, excluded from summaries | 3 seconds, excluded from summaries |
| Measurement | 20 seconds | 20 seconds |
| Authentication | Login before warm-up; reuse authorized session | Separate sessions or explicit documented shared test identity |
| Executed candidate response threshold | p95 under 750 ms | p95 under 750 ms |
| Unexpected error threshold | under 1% | under 1% |

These short runs are ordinary/peak **load** evaluations only. They are not endurance, stress-to-failure, production capacity or internet-latency claims. Record actual hardware, OS, Python/Flutter/library versions, source/build identification, database settings/size, processes and deployment scheme. Do not compare measurements across changed environments without accounting for those changes.

Collect each request's time/status/latency and the scenario identity. Summarize p50/p95/p99, completed requests per measured second, and unexpected failures. Expected 4xx from separate negative/security cases must not inflate the ordinary-load unexpected error calculation. Report timeouts and connection errors explicitly rather than dropping samples. Capture backend process CPU/RSS where supported with sampling interval and measurement limitations; CPU attribution excludes the browser/worker unless actually included.

Read-heavy journeys assess ordinary review responsiveness. Write correctness and stale/conflict/idempotency behavior are covered by functional/concurrency tests; a report-only load test does not establish write capacity. If write traffic is included, document stable data setup and expected conflict handling so workload state remains interpretable.

Interpretation template: observed counts and percentiles → candidate threshold comparison → plausible bottleneck with supporting evidence → next measurement. A low response time on one laptop does not establish deployment readiness. Compare the same model and dataset in development and controlled deployment when both can actually run; otherwise label configuration inspection separately.
