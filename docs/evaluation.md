# SA9 / AS3 integrated technical evaluation

Technical evaluation reconciled with actual backend, Flutter, automation, security, workload, TLS and restoration artifacts. Browser and final source/publication status must match the final evidence index; participant assessment remains separate. Do not treat the presence of this report as proof of UAT or institutional acceptance.

| Quality | Required support | Interpretation limit |
|---|---|---|
| Functional/interoperability | Flutter/API normal path, schemas/status/serialization, persisted report/audit | Cases and versions actually tested |
| Security | Role/class/session/CSRF/validation/exchange/TLS negatives and safe configuration | No absolute security or independent penetration-test claim |
| Reliability | Bounded retry/permanent routing/deduplication/restart and recovery | Local provider only unless external delivery actually tested |
| Performance | Defined workload and raw percentiles/throughput/errors/resource observations | Test hardware/mix/duration, not production capacity |
| Usability | State/layout tests and genuine role UAT observations | Developer checks are not independent UAT |
| Maintainability | Small components, configuration, migrations, diagrams/ADR/OpenAPI/runbooks | Requires owner and ongoing work |
| Operational readiness | Health/monitoring/environment/recovery checks and conditional recommendation | Controlled prototype; no production authorization |

Architecture recommendation and sensitivity are in `docs/decisions/architecture.md`. UAT criteria/findings/dispositions are in `docs/uat/plan-and-records.md` and remain participant-pending where no session was conducted. Maintenance and role ownership are in `docs/maintenance.md`; recovery/readiness in deployment docs; technical source/test artifacts in the evidence index.

Final report should state demonstrated strengths, observed failures and fixes, unverified controls/environments, open risks, human-required activities and realistic next improvements. Distinguish observed facts from reasoned conclusions and future recommendations. The authorized reviewer decides assessment acceptance; the repository documents bounded capability and honest limitations.

## Observed technical support

- Backend: final 40 passing tests after three genuine corrected root causes, with original failures retained and sanitized; statement coverage658/761 (86.465%),103 uncovered, no complete-path claim (`evidence/week15/backend-tests.*`, `coverage.json`, `docs/testing/hardening-record.md`).
- Client state/layout: 11 passing Flutter tests including 390/768/1440 widths; static analysis no issues; web release build succeeds. These isolate client state with a fake API; browser integration is a separate artifact.
- Automation: four actual controlled-clock normal/transient/permanent/exhaustion cases pass with bounded attempts and at most one controlled-event inbox delivery (`evidence/week13/automation.json`).
- Security: eight in-process integration checks pass, supplemented by backend expiry/wrong-key/role/class/password cases (`evidence/week14/security.json`); actual explicit-CA HTTPS and untrusted rejection pass separately (`evidence/week16/tls.json`).
- Performance: ordinary 276 requests at p95 22.581 ms; peak 3062 at p95 44.702 ms; both zero unexpected errors and below predefined 750 ms/<1% script thresholds. Short read-heavy one-host scope is explained in `performance/results.md`.
- Recovery: consistent snapshot restores 12 students, removes controlled mutation, passes integrity, then saves/finalizes through restored API (`evidence/week16/recovery.json`). Full infrastructure rollback is a procedure, not an observed exercise.
- Deployment: actual loopback HTTP versus explicit-CA HTTPS configuration and worker restart evidence are in `evidence/week16/deployment.json`; no independent server/cloud availability claim.

- Browser: actual Chrome148 run (`evidence/week18/browser/results.json`) passed8 checks with0 page errors: required fields,teacher login/save/finalize,persisted report/audit,unavailable-service retry,768/390 captures,keyboard focus,anonymous401. Desktop1440/tablet768/mobile390 images were inspected. These are developer checks, not independent participant feedback.
- Worker restart: actual changed process and advanced heartbeat; persisted notification delivered on attempt2; post-restart readiness200. Windows startup/stop scripts were also smoke-tested against owned recorded processes.

Reasoned recommendation: **conditionally ready for a controlled fictional-data classroom demonstration in the tested Windows single-host environment**. Required technical behavior is supported by actual API/widget/browser/automation/security/TLS/workload/recovery checks. Independent UAT/peer/viva/reflection and production authorization remain pending; broader use needs the actions in `known-limitations-and-risks.md` and the architecture review conditions.
