# Actual ordinary and peak workload results

Source artifact: `evidence/week16/performance.json`, executed 2026-11-08 14:45:06 UTC (22:45:06 Asia/Manila). The manifest records Python 3.13.17 on Windows 11 build 26200, the prior Git HEAD plus the actual working-tree source hash/file inventory. Performance source SHA-256: `9ca67317c2d8c35eb14945f4ebcac27d2fff250cdf2e3ae70a3e7b7ba0baa831`. A Git HEAD alone would not identify the uncommitted implementation, so retain that source inventory.

The live loopback API was measured with 1 class, 12 fictional learners, and 1 session. Each simulated client authenticated independently using the teacher role. Mix: 50% dashboard, 30% session list, 20% reports. Warm-up was 3 seconds, measurement target 20 seconds; nearest-rank percentiles are calculated from retained per-request latency samples. Each read expected 200; unexpected HTTP/network outcomes are counted, not discarded. No expected negative/security requests are included in this workload's error denominator.

| Actual metric | Ordinary | Peak |
|---|---:|---:|
| Concurrent clients | 3 | 12 |
| Think time (s) | .20 | .05 |
| Measured elapsed (s) | 20.186 | 20.084 |
| Completed requests | 276 | 3062 |
| p50 (ms) | 9.984 | 22.856 |
| p95 (ms) | 22.581 | 44.702 |
| p99 (ms) | 35.711 | 60.522 |
| Throughput (requests/s) | 13.673 | 152.460 |
| Unexpected errors | 0 | 0 |
| Unexpected error rate | 0% | 0% |
| Script candidate p95 threshold | <750 ms | <750 ms |
| Script candidate error threshold | <1% | <1% |
| Recorded threshold outcome | Met | Met |

Resource samples refer to the owned API process, not total machine/browser/worker load. The JSON retains the raw samples and latencies.

| Resource observation | Ordinary | Peak |
|---|---:|---:|
| Samples | 78 | 79 |
| API-process CPU mean (sample arithmetic mean) | 7.48% | 124.85% |
| API-process CPU maximum | 24.8% | 192.4% |
| RSS minimum (bytes) | 60,313,600 | 61,759,488 |
| RSS maximum (bytes) | 60,563,456 | 63,528,960 |

`psutil` process CPU can exceed 100% across logical CPUs: 124.85% is roughly 1.25 fully occupied logical cores, not 124.85% of the whole host. CPU sample intervals and the initial priming/warm-up interval differ from per-request timing; do not treat the arithmetic sample mean as a separately established machine-wide utilization measurement.

Same-host hardware inspection during result reconciliation: Intel64 Family 6 Model 186 Stepping 3, GenuineIntel; 10 physical and 12 logical CPUs reported by `psutil`; total visible memory 16,806,244,352 bytes. This describes the test host, not a portable capacity guarantee.

```powershell
.\.tools\python\python.exe -m scripts.performance --pid <owned-API-process-id>
```

Prefer `python -m scripts.evaluate` for owning the controlled processes and fixture. The performance script writes fresh results; preserve previous runs under distinct names if comparing them.

Observed fact: both short read-heavy models met their predefined script thresholds without unexpected errors. Reasoned conclusion: this small local API dataset supports responsive ordinary/peak review in the tested configuration. Limits: one host, loopback HTTP, one small dataset, one run per model, short duration, read traffic, no internet latency, no stress/endurance, no write-capacity estimate, and no independently provisioned server. Next measurements should repeat runs with larger historical data and mixed writes before proposing broader deployment.
