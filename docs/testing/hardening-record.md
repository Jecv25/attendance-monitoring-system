# Actual hardening findings and regression evidence

This record describes genuine failures preserved during implementation, not the isolated weak-configuration exercise. Source paths refer to the implementation working tree; final source/build identification is recorded in the completion report/evidence index. No test password, cookie, token or encryption key is reproduced here.

## Observed runs

| Artifact | JUnit start time (Asia/Manila, +08:00) | Actual outcome |
|---|---|---|
| `evidence/week15/backend-before.xml` and `.log` | 2026-11-08 22:27:12 | 36 tests: 5 failed, 31 passed, 0 errors; suite time 9.074 s |
| `evidence/week15/password-before.xml` and `.log` | 2026-11-08 22:28:08 | Targeted password case: 1 failed, 0 errors; .500 s |
| Intermediate passing run observed before expanded suite; current result files supersede it | 2026-11-08 22:28:40 | 36 tests passed, 0 failures/errors; JUnit 9.148 s, pytest summary 9.14 s |
| Final `evidence/week15/backend-tests.xml` and `.log` | 2026-11-08 22:48:36 | 40 tests passed, 0 failures/errors; JUnit 13.787 s, pytest summary 13.79 s |

Preserved failure logs/XML were sanitized to redact incidental generated test credentials and normalize text encoding; their failure assertions and result counts remain intact. Final staged-publication review must still check for unintended sensitive material. Raw ephemeral credentials are unnecessary to reproduce the defect: fixtures generate fresh test-only values.

## Three corrected weaknesses

| ID / priority | Genuine before observation | Cause and implemented correction | Original-case rerun and relevant regression |
|---|---|---|---|
| HARD-01 / P1 functional integration | `test_dashboard_real_request` returned 500 rather than 200. Report-exchange setup also returned 500, and unavailable-key handling returned 500 instead of intended 503. All three failures are in `backend-before.xml`. | Direct Python calls to a FastAPI route inherited `Query` marker defaults instead of concrete values. `backend/app/main.py` now separates `build_report(...)` with plain Python defaults from the HTTP route; dashboard and sender use the helper. | `test_dashboard_real_request`, `test_exchange_tamper_replay_wrong_key_and_expiry`, and `test_exchange_unavailable_key` pass in the final 40-test suite; normal save/finalize/report/audit and contract checks also pass. |
| HARD-02 / P1 boundary consistency | Rejected Origin response lacked `X-Content-Type-Options: nosniff`/no-store; oversized-body rejection lacked correlation ID. Two actual failed assertions are in `backend-before.xml`. | Early middleware returns skipped shared security headers and request decoration. Rejections now become responses passed through the common decoration/logging path in `backend/app/main.py`. | `test_security_headers_on_rejected_origin` and `test_security_headers_on_oversize_body` pass; normal cookie/security-header checks pass in the same suite. |
| HARD-03 / P1 credential semantics | `test_password_whitespace_preserved` observed a normalized password being accepted (200) where a distinct credential should return 401; targeted failure is in `password-before.xml`. | Inherited string normalization changed password semantics. `backend/app/schemas.py` now explicitly preserves whitespace for password creation/reset and login, using bounded password constraints with stripping disabled. | The original password succeeds while its trimmed variant is rejected in `test_password_whitespace_preserved`; final authentication/session/rate-control tests pass in the same suite. |

These priorities reflect exposed workflow/security boundary impact, not a claim that an attacker exploited the prototype. Three root causes account for more than three failed assertions. They were discovered through source review and real tests, rather than planted defects.

Reproduction command from repository root using the workspace-local Python runtime:

```powershell
.\.tools\python\python.exe -m pytest backend/tests -q --junitxml=evidence/week15/backend-tests.xml
```

If using an installed Python/virtual environment instead, use that interpreter with the same project dependencies. Keep original pre-fix artifacts unchanged except necessary redaction; write new rerun output to a distinct filename.

## Coverage and remaining limits

The final backend suite exercises normal registration/attendance/finalization/report/audit, invalid/atomic batch input, roster snapshots, stale/idempotency conflicts, true concurrent writes (one success and one conflict), corrections, batch/field/date limits, finalization deduplication, last-admin protection, authentication/logout/expiration, CSRF/role/class checks, cookie hashing/headers, OpenAPI cookie/header declarations, report tamper/wrong-key/expiry/replay/unavailable-key behavior, worker retry/permanent/exhaustion/deduplication/lease recovery/timeout, missed-session behavior, readiness and manual alert recovery. Actual line coverage is 658/761 statements, 86.465% (`evidence/week15/coverage.json`); 103 statements remain uncovered. This is not branch coverage or proof that every possible path is correct.

The backend suite itself does not establish Flutter/browser results, trusted HTTPS, measured deployment performance, a real process-restart exercise, external email/SMS, independent penetration testing, or stakeholder UAT. Separate subsequently collected artifacts are listed below and in the root evidence index. The pytest log reports one upstream `StarletteDeprecationWarning` concerning TestClient's `httpx` integration; tests passed, but dependency compatibility should be reviewed during maintenance rather than hiding the warning.

## Additional actual frontend and transport findings

`evidence/week15/flutter-before.log` preserves an initial 7 passed / 4 failed widget run. A missing Material ancestor around sidebar ListTiles and a long sidebar label caused assertions and a 48-pixel right overflow. `frontend/lib/workspace.dart` now supplies a Material sidebar and bounds the label with a single-line ellipsis. `flutter-tests.log` records all 11 tests passing, including layouts at 390, 768 and 1440 pixels, unsaved-selection/idempotent retry, explicit finalization and read-only Supervisor controls. These tests use a fake API to isolate client state; real API integration requires separate browser evidence.

`flutter-analyze.log` records no issues. Recorded `flutter-build.log` succeeds with `flutter build web --no-web-resources-cdn` in 39.8 seconds (an earlier observed build took 37.4 seconds). Subsequent starter-description/manifest cleanup has its own successful metadata-only rebuild output in `flutter-build-final.log`; read that artifact for its duration. No Dart behavior changed after the passing browser run. PowerShell captured the informational successful Wasm dry-run message as a NativeCommandError-formatted stderr entry; the successful build logs explicitly end with web output. This was a JavaScript web release with an informational Wasm compatibility check, not a claim that a Wasm build was tested.

`evidence/week16/tls-before.json` preserves a real strict-certificate failure (missing Authority Key Identifier). Generated certificate authority/subject key identifiers and key usages were corrected; `tls.json` records subsequent trusted-CA success, untrusted rejection and secure HTTPS exchange. Exact initial-command timestamp was not retained; only the known date and actual error are recorded. See `docs/deployment/verification.md` for scope.

Browser initial/second locator-timeout failures remain in `evidence/week18/browser/failure.json` and `attempt2-failure.json` with screenshots. The captured login had empty-password validation, not a demonstrated API-authentication rejection. A lifetime `SemanticsHandle` keeps the app's accessibility tree available; the harness uses actual keyboard input, scrolling and synchronized actions. Final `results.json` records 8 passing checks and no page errors, including real teacher save/finalize200, report/audit persistence, unavailable-service retry, 768/390 captures, keyboard focus and anonymous401. API and browser findings are distinguished rather than relabeling a harness failure as a backend defect.
