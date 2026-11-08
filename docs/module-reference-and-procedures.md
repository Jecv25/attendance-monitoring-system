# Module reference and common hands-on coverage

Academic requirements source: user-provided *PFEBSIT 002 Weeks 13–18 Student Module, Flutter Web*, University of La Salette, AY 2026–2027. It is the requirements reference, not a substitute for actual implementation evidence or human assessment. The selected attendance scope was authorized by the user; no instructor approval document has been supplied.

Full DOCX XML inspection found 18 hands-on `Procedure` blocks: three phases per week, with the same seven steps in each phase across all six weeks. The coverage below paraphrases those 21 distinct steps; weekly domain-specific descriptions, topics, activities, assessments and rubrics remain mapped separately in `REQUIREMENTS_TRACEABILITY.md`.

| Common procedure | Attendance interpretation and artifact | Verification boundary |
|---|---|---|
| H1.1 Feature branch, evidence folder, dated environment/runtime/scope lab record | Git source state, `evidence/`, `docs/laboratory-log.md` | Record real branch/commit chronology; do not claim earlier branch creation or instructor approval |
| H1.2 Actors/trigger/trusted input/validation/processing/output/dependencies/non-goals | `architecture/boundary-and-data-flow.md` | Prepared design; runtime behavior tested separately |
| H1.3 Diagram trust, credentials, sensitive data, logs, failure and human decisions | Boundary/data-flow and sequence diagram | Keys shown as protected source, never actual secret values |
| H1.4 Measurable normal/invalid/unauthorized/unavailable/recovery criteria | `testing/test-strategy.md`; UAT criteria | Technical and participant evidence distinct |
| H1.5 Fictional data and secret-free example config | Management seed, `.env.example` | Check source/staged files; no production endpoint/real record |
| H1.6 Selected approach and at least one alternative | `decisions/architecture.md` | Reasoned choice, disadvantages and review conditions |
| H1.7 UI flow/reuse/validation/responsiveness/API states/feedback | `architecture/screen-flow.md`; Flutter widgets | Widget/browser evidence needed for runtime claims |
| H2.1 Smallest separated end-to-end scenario | Flutter → API → database normal path | Actual API/browser evidence; no mock substitution |
| H2.2 Authoritative boundary validation and safe errors | Backend schemas/domain/middleware | Negative tests and protected diagnostics |
| H2.3 External protected configuration | Local setup + ignored `.env` | Placeholder example and redacted scan |
| H2.4 Structured correlation logs of safe state/outcome | API and worker event logs | Safe event fields; no credentials/bodies |
| H2.5 Success plus at least four repeatable adverse paths | API/security/worker/UI suites | Actual expected/actual/timestamp records |
| H2.6 Commit working increment with behavior/evidence message | Real Git commits | Preserve genuine chronology, not invented historical commits |
| H2.7 Real API-connected Flutter screens and browser states | Frontend + state/browser suite | Loading/success/validation/auth/forbidden/empty/failure |
| H3.1 Predict and inject one controlled relevant failure | Adapter and failure/security exercises | Preserve initial prediction and actual outcome |
| H3.2 Bounded safe failure and actionable signal | Retry ceiling, safe errors, escalation | No corrupt attendance, leaked secrets or infinite retries |
| H3.3 Justified improvement and original-case/regression rerun | `testing/hardening-record.md` | Three genuine corrected root causes supported by retained failures |
| H3.4 Counts/timings/logs and observation versus interpretation | Raw evidence + reports | Measurements must be actual; infer only within scope |
| H3.5 Matching README/ADR/diagram/limitations/recovery | Root README + docs/runbooks | Final source/document audit |
| H3.6 Controlled short demo and fallback | `defense/demo.md`; real run artifacts | No fabricated screenshot or substituted mock live claim |
| H3.7 Desktop/narrow workflow, form/server agreement and recovery | Flutter tests and browser evidence | Actual viewport/keyboard/save-failure checks |

## Reference inventory listed by the module

These are bibliographic entries in the supplied module, not a claim that every source was independently consulted or its publication metadata verified during this project. The academic requirements citation remains the module. Installed dependency manifests and actual implementation research should identify any additional official technical documentation used.

| Module-listed source | Locator / subject |
|---|---|
| Bucko, Vishi, Krasniqi & Rexha (2023), *Enhancing JWT authentication and authorization in web applications based on user behavior history*, Computers 12(4),78 | Module secondary reference; the prototype uses server-side sessions, not JWT |
| Geewax (2021), *API design patterns*, Manning | Module secondary reference |
| GitHub, About READMEs | https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes |
| Google, Site Reliability Engineering | https://sre.google/sre-book/table-of-contents/ |
| Gowda & Gowda (2024), *Best practices in REST API design for enhanced scalability and security*, Journal of Artificial Intelligence, Machine Learning and Data Science 2(1),827–830 | Module secondary reference |
| Microsoft, Azure Architecture Center | https://learn.microsoft.com/azure/architecture/ |
| Microsoft, Circuit Breaker pattern | https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker |
| Microsoft, Retry pattern | https://learn.microsoft.com/azure/architecture/patterns/retry |
| NIST, SP 800-132 password-based key derivation | https://csrc.nist.gov/publications/detail/sp/800-132/final |
| NIST, AES FIPS 197-upd1 | https://doi.org/10.6028/NIST.FIPS.197-upd1 |
| OpenAPI Initiative, OpenAPI 3.1.1 | https://spec.openapis.org/oas/v3.1.1.html |
| OpenTelemetry documentation | https://opentelemetry.io/docs/ |
| OWASP ASVS | https://owasp.org/www-project-application-security-verification-standard/ |
| OWASP API Security Top 10 | https://owasp.org/API-Security/ |
| OWASP Cryptographic Storage Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html |
| Postman Learning Center | https://learning.postman.com/ |
| Shukla (2025), *Exploring the integration of APIs in microservices for scalable application development*, Journal of Recent Trends in Computer Science and Engineering 13(1),23–30 | Module secondary reference |

The generated API may advertise an installed framework's compatible OpenAPI 3.1 patch level. Record the actual version instead of relabeling output as 3.1.1 without validation. The module's references do not require adding JWT, microservices, a circuit breaker, OpenTelemetry, Azure, or Postman when an explicitly justified equivalent meets the bounded requirement.
