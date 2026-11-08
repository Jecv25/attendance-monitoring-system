# Laboratory chronology

This log records known events without inventing approvals, branch timing or human assessment. Final source/build and environment identifiers are completed in the root evidence index and completion report.

| Event | Evidence / actual outcome |
|---|---|
| User scope selected | Attendance Monitoring System; Flutter Web, API, bounded automation/security/testing/deployment/UAT/defense portfolio. Instructor/stakeholder approval not supplied. |
| Repository preparation | Existing source history retained; prior cleanup commit `2c1d40f5fe72676a856e803a2b8059702bd7afad` removed legacy project files before this implementation. |
| Preimplementation requirements | Initial 80-row `REQUIREMENTS_TRACEABILITY.md` created before the implementation increment; source module phases/topics/activities/rubrics mapped. |
| Source design and implementation | Separated FastAPI/SQLite/worker and Flutter Web; architecture/source details in docs and actual repository. Runtime versions belong in execution manifests. |
| 2026-11-08 22:27:12 +08:00 | First backend JUnit run: 36 tests, 5 failures and 31 passes; original artifacts preserved in `evidence/week15/backend-before.*`. |
| 2026-11-08 22:28:08 +08:00 | Targeted password-semantics failure preserved in `evidence/week15/password-before.*`; incidental generated credential values were later redacted while retaining actual outcomes. |
| 2026-11-08 22:28:40 +08:00 | Intermediate corrected regression observed: 36 passed,0 failed/errors,JUnit9.148 seconds. Current `backend-tests.*` files supersede that intermediate run with the expanded final40-test result. |
| Frontend verification | Original widget run7 passed/4 failed; final11 passed; analysis no issues; recorded release build39.8 seconds (earlier observed37.4). Metadata-only starter-description/manifest cleanup has separate `flutter-build-final.log` output; it does not change Dart behavior verified by the browser. |
| 2026-11-08 14:39:44 UTC (22:39:44 +08:00) | Four controlled-clock automation cases and eight in-process security checks passed; JSON manifests retain working-tree source inventories. |
| 2026-11-08 14:39:45 UTC (22:39:45 +08:00) | Isolated SQLite restoration passed integrity/count/mutation checks, followed by attendance save/finalize200 (`evidence/week16/recovery.json`). |
| 2026-11-08 14:45:06 UTC (22:45:06 +08:00) | Ordinary/peak read workload manifest:276/3062 requests,p95 22.581/44.702 ms,zero unexpected errors. |
| TLS/deployment | Strict certificate failure preserved, generated certificate extensions corrected, actual explicit-CA TLS passes; local HTTP/HTTPS profiles and worker-process result recorded in `evidence/week16/`. |
| 2026-11-08 22:48:36 +08:00 | Expanded final backend regression40 passed,0 failures/errors,JUnit13.787 seconds; statement coverage658/761 (86.465%). Earlier36-pass run is historical; current result files reflect expanded suite. |
| 2026-11-08 14:52:41 UTC (22:52:41 +08:00) | Actual developer browser8 checks passed,0 page errors; desktop/tablet/narrow screenshots retained. Original harness/input-timeout failures are preserved separately. |
| Final live restart | Changed actual worker PID,advanced heartbeat,persisted notification delivered on attempt2,readiness200. Same host/configuration comparison only. |
| Startup scripts | Actual `run.ps1 -SkipBuild` yielded database/worker readiness true; `stop.ps1` stopped the recorded owned processes. |
| Branches and commits | Actual local `feat/attendance-system` created after coding and before initial implementation commit; main delivery follows normal commit/fast-forward/push. Final report/Git history records actual results; no pre-code feature branch is claimed. |
| UAT/peer review/mock defense/viva/reflection | Pending actual representative participants and student work; prepared materials are not completion claims. |

Dates above come from actual JUnit timestamps with +08:00 offset (Asia/Manila). Preserve original failures and subsequent reruns. Development configuration and generated credentials remain ignored and must not enter screenshots, logs or source publication.
