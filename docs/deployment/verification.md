# Actual controlled deployment and recovery verification

Read the JSON manifests for exact execution time, source-file hashes, command and environment. These are actual local checks, not public hosting or independent-server evaluation.

| Artifact | Actual observation | Scope |
|---|---|---|
| `evidence/week16/recovery.json` | Integrity `ok`; 12 students before and restored; controlled name mutation absent from restored snapshot; attendance save 200; finalization 200 | Real isolated SQLite snapshot/restoration through backup API and restored FastAPI application; not full host rollback |
| `evidence/week16/tls-before.json` | First strict trusted-CA handshake failed: missing Authority Key Identifier | Genuine original interoperability failure; exact command timestamp was not retained and is not invented |
| `evidence/week16/tls.json` | Explicit local CA accepted, default untrusted certificate rejected, Secure/HttpOnly cookie and HSTS present, encrypted sender/receiver over HTTPS returned 200 | Actual separate local HTTPS process; no disabled validation or system/browser trust change |
| `evidence/week16/deployment.json` | HTTP development profile port 8000/Secure false versus HTTPS evaluation port 8443/Secure true; readiness200; changed worker PID; advanced heartbeat; persisted event delivered after restart on attempt2; post-restart readiness200 | Same host and database, separate local process/configuration profiles; actual replacement process and persistent-work recovery |

The TLS fix in `scripts/tls.py` adds authority/subject key identifiers and explicit key usages to generated CA/leaf certificates, retains strict certificate validation, and supports controlled `--rotate`. CA key is not retained; leaf certificate lasts 7 days and local CA 30 days. This exercise does not provision a publicly trusted certificate or endorse weakening verification.

The recovery fixture checks the resolved dedicated `.local/exercises/` path, takes a consistent snapshot, performs a controlled mutation in the exercise source, restores into another database, checks integrity/count/name, then authenticates, saves and finalizes through the restored application. Existing demonstration data is not overwritten.

Worker recovery has two distinct supports: automated tests cover persisted attempts, deduplication and expired leases; final live evaluation records a changed actual worker process, advanced heartbeat and persisted event delivered on attempt2. Readiness alone can remain briefly true from an old heartbeat, so the evaluator was strengthened to establish process/heartbeat advancement rather than interpreting a 200 in isolation. This supports the tested single-host restart; it does not establish distributed failover.

Reproduction from repository root after setup/release build:

```powershell
$taskPython = '.\.tools\python\python.exe'
& $taskPython -m scripts.exercises
& $taskPython -m scripts.tls
& $taskPython -m scripts.evaluate
```

Use the evaluation script's supported skip-performance option when independently rerunning unchanged browser/TLS/restart checks and retaining the existing workload measurement. Preserve original failures and distinguish later source inventories in the manifests.
