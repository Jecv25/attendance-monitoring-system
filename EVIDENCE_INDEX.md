# Evidence index

The supplied module is the academic requirements source. [Traceability](REQUIREMENTS_TRACEABILITY.md) maps each weekly topic, activity, hands-on phase, assessment and shared condition. Runtime records identify their source fingerprints, environment, fictional data and scope. Source fingerprints refer to the execution snapshot; later documentation/harness edits do not retroactively change measured results.

| Requirement / evidence | Actual artifact | Result and boundary |
|---|---|---|
| W13 normal/retry/permanent/exhausted delivery | [Automation](evidence/week13/automation.json) | Four scenarios passed. Controlled clock advances are explicitly distinguished from wall-clock performance. |
| W13 correlation/state logging | [HTTP events](evidence/week13/http-structured.jsonl), [worker events](evidence/week13/worker-structured.jsonl) | Actual safe request/transition records, without credentials. |
| W13 missed sessions/deduplication/leases/timeout | [Backend tests](evidence/week15/backend-tests.xml), `backend/tests/test_worker.py` | Pending students remain unmarked; notification attempts are bounded. |
| W14 protected exchange and negative cases | [Security exercise](evidence/week14/security.json), [security tests](backend/tests/test_security.py) | Eight scripted checks plus expiry/wrong-key/role/object tests. In-process integration here; HTTPS transport below. |
| W14 HTTPS / secure cookie / invalid certificate | [TLS](evidence/week16/tls.json) | Explicit CA validation, rejection of untrusted certificate, Secure/HttpOnly cookie, HSTS, encrypted sender/receiver200. |
| W14 strict TLS defect | [Original failure](evidence/week16/tls-before.json) | Missing Authority Key Identifier corrected; certificate validation retained. |
| W15 original backend failures | [Initial JUnit](evidence/week15/backend-before.xml), [log](evidence/week15/backend-before.log), [password case](evidence/week15/password-before.xml) | Genuine failures preserved. Ephemeral test credential values redacted; outcomes unchanged. |
| W15 backend/API regression | [Final JUnit](evidence/week15/backend-tests.xml), [log](evidence/week15/backend-tests.log), [coverage](evidence/week15/coverage.json) | 40 passed; 86.465% statement coverage. One test-client deprecation warning. Includes actual concurrent writes and schema/header discoverability. |
| W15 Flutter original defects | [Original output](evidence/week15/flutter-before.log) | Seven passed/four failed before sidebar Material/overflow fixes. |
| W15 Flutter state and responsive tests | [Final output](evidence/week15/flutter-tests.log), [tests](frontend/test/workflow_test.dart) | 11 passed, including390/768/1440px, unsaved-entry preservation and retry key reuse. |
| W15 static analysis / release build | [Analysis](evidence/week15/flutter-analyze.log), [tested build](evidence/week15/flutter-build.log), [final metadata build](evidence/week15/flutter-build-final.log) | No analysis issues; web release built. Informational Wasm dry-run message does not establish a Wasm deployment. |
| W16 ordinary and peak workload | [Raw results](evidence/week16/performance.json), [interpretation](docs/performance/results.md) | 276/3062 reads, zero unexpected errors, p95 22.581/44.702ms; same-host, small-data, short-run limits. |
| W16 consistent backup and restoration | [Recovery](evidence/week16/recovery.json) | Twelve fictional students restored, integrity ok, save and finalize200 afterward. |
| W16 profiles/readiness/process restart | [Deployment](evidence/week16/deployment.json) | HTTP/HTTPS profiles verified. New PID, advanced heartbeat and persisted leased event delivered on attempt2. |
| W17 technical walkthrough | [Developer verification](evidence/week17/README.md), [browser results](evidence/week18/browser/results.json) | Developer verification only; independent UAT remains pending. |
| W17 representative UAT | [UAT plan](docs/uat/plan-and-records.md), [record sheet](evidence/week17/uat-records.csv) | Pending Human Participation; no fabricated findings or sign-off. |
| W18 normal/browser/adverse/recovery/fallback | [Browser results](evidence/week18/browser/results.json), [demo](docs/defense/demo.md), [internal review](evidence/week18/internal-review.md) | Eight browser checks passed, no application page errors. Earlier harness failures remain labeled as harness failures. |
| W18 peer/viva/contribution/reflection | [Defense materials](docs/README.md) | Prepared materials; actual human assessment remains pending. |
| All source/config/publication checks | [Repository audit](evidence/week18/repository-audit.json), [verification environment](evidence/week18/environment.json) | Final artifact/secret/link review and source/environment record. |

Actual screenshots: [desktop dashboard](evidence/week18/browser/02-dashboard-desktop.png), [saved attendance](evidence/week18/browser/03-attendance-saved.png), [finalized attendance](evidence/week18/browser/04-attendance-finalized.png), [report](evidence/week18/browser/05-reports-desktop.png), [audit](evidence/week18/browser/06-audit-desktop.png), [unavailable service](evidence/week18/browser/07-unavailable-service.png), [tablet](evidence/week18/browser/08-dashboard-768.png), [narrow browser](evidence/week18/browser/08-dashboard-390.png).

Screenshots support the executable source and tests; they do not establish production readiness or participant acceptance.
