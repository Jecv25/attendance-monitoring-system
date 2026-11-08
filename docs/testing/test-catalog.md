# Executed test catalog

Generated from actual final JUnit; fixtures and preconditions are in `backend/tests/conftest.py`. The [test strategy](test-strategy.md) supplies risk/ownership/exit criteria. [JUnit](../../evidence/week15/backend-tests.xml) records actual outcomes and execution times; [environment](../../evidence/week18/environment.json) identifies tool/source context.

| Test ID | Requirement family | Executable case | Expected result | Actual result |
|---|---|---|---|---|
| API-001 | WEB-01 / W15-02 | [test_normal_save_finalize_report_audit](../../backend/tests/test_api.py) | Save/finalize200; persisted report counts and audit agree | Passed |
| API-002 | WEB-01 / W15-02 | [test_dashboard_real_request](../../backend/tests/test_api.py) | Dashboard200 and one visible session | Passed |
| API-003 | WEB-01 / W15-02 | [test_admin_registration_path](../../backend/tests/test_api.py) | Student/class/session201; duplicate session409 | Passed |
| API-004 | WEB-01 / W15-02 | [test_pending_and_finalization_rules](../../backend/tests/test_api.py) | Two pending learners; incomplete finalization422 | Passed |
| API-005 | WEB-01 / W15-02 | [test_idempotent_retries_and_key_payload_conflict](../../backend/tests/test_api.py) | Same request200 once; changed payload409; two records and one audit | Passed |
| API-006 | WEB-01 / W15-02 | [test_conflict_and_correction](../../backend/tests/test_api.py) | Stale/ordinary finalized writes409; reasoned correction200; short reason422 | Passed |
| API-007 | WEB-01 / W15-02 | [test_invalid_attendance_is_atomic[payload0]](../../backend/tests/test_api.py) | Invalid request422 and zero attendance mutations | Passed |
| API-008 | WEB-01 / W15-02 | [test_invalid_attendance_is_atomic[payload1]](../../backend/tests/test_api.py) | Invalid request422 and zero attendance mutations | Passed |
| API-009 | WEB-01 / W15-02 | [test_invalid_attendance_is_atomic[payload2]](../../backend/tests/test_api.py) | Invalid request422 and zero attendance mutations | Passed |
| API-010 | WEB-01 / W15-02 | [test_invalid_attendance_is_atomic[payload3]](../../backend/tests/test_api.py) | Invalid request422 and zero attendance mutations | Passed |
| API-011 | WEB-01 / W15-02 | [test_invalid_attendance_is_atomic[payload4]](../../backend/tests/test_api.py) | Invalid request422 and zero attendance mutations | Passed |
| API-012 | WEB-01 / W15-02 | [test_invalid_attendance_is_atomic[payload5]](../../backend/tests/test_api.py) | Invalid request422 and zero attendance mutations | Passed |
| API-013 | WEB-01 / W15-02 | [test_atomic_mixed_roster_rejection](../../backend/tests/test_api.py) | Mixed invalid roster422; earlier entries rolled back | Passed |
| API-014 | WEB-01 / W15-02 | [test_roster_snapshot_survives_changes](../../backend/tests/test_api.py) | Class roster edit200; original session roster count preserved | Passed |
| API-015 | WEB-01 / W15-02 | [test_not_found_and_boundary_limits](../../backend/tests/test_api.py) | Missing session404; invalid pagination/date bounds422 | Passed |
| API-016 | WEB-01 / W15-02 | [test_schedule_boundaries[2026-11-09T09:00:00-2026-11-09T10:00:00]](../../backend/tests/test_api.py) | Naive, reversed or greater-than24h schedule422 | Passed |
| API-017 | WEB-01 / W15-02 | [test_schedule_boundaries[2026-11-09T10:00:00Z-2026-11-09T09:00:00Z]](../../backend/tests/test_api.py) | Naive, reversed or greater-than24h schedule422 | Passed |
| API-018 | WEB-01 / W15-02 | [test_schedule_boundaries[2026-11-09T09:00:00Z-2026-11-11T09:00:00Z]](../../backend/tests/test_api.py) | Naive, reversed or greater-than24h schedule422 | Passed |
| API-019 | WEB-01 / W15-02 | [test_api_contract](../../backend/tests/test_api.py) | OpenAPI3.1, strict schema, cookie and CSRF/idempotency discoverability | Passed |
| API-020 | WEB-01 / W15-02 | [test_real_concurrent_updates_have_one_winner](../../backend/tests/test_api.py) | Concurrent same-version writes return one200 and one409 | Passed |
| API-021 | WEB-01 / W15-02 | [test_finalization_retry_does_not_duplicate_event](../../backend/tests/test_api.py) | Repeated finalization200 with one durable event | Passed |
| API-022 | WEB-01 / W15-02 | [test_batch_and_roster_limits](../../backend/tests/test_api.py) | More than100 roster or attendance entries422 | Passed |
| API-023 | W14-05 / W15-04 | [test_unauthenticated_invalid_and_expired_sessions](../../backend/tests/test_security.py) | Each protected request401 | Passed |
| API-024 | W14-05 / W15-04 | [test_role_object_access_and_csrf](../../backend/tests/test_security.py) | Cross-class, forbidden role and wrong-CSRF requests403 | Passed |
| API-025 | W14-05 / W15-04 | [test_logout_revokes_session](../../backend/tests/test_security.py) | Logout200, subsequent session access401 | Passed |
| API-026 | W14-05 / W15-04 | [test_invalid_login_rate_limit_and_safe_validation](../../backend/tests/test_security.py) | Eight failures401, next429; validation422 without secret input | Passed |
| API-027 | W14-05 / W15-04 | [test_cookie_hash_and_security_headers](../../backend/tests/test_security.py) | Opaque token stored hashed; Argon2id and required response headers | Passed |
| API-028 | W14-05 / W15-04 | [test_security_headers_on_rejected_origin](../../backend/tests/test_security.py) | Untrusted origin403 with common security/no-store headers | Passed |
| API-029 | W14-05 / W15-04 | [test_security_headers_on_oversize_body](../../backend/tests/test_security.py) | Oversize413 with correlation identifier | Passed |
| API-030 | W14-05 / W15-04 | [test_password_whitespace_preserved](../../backend/tests/test_security.py) | Exact password200; whitespace-normalized alternative401 | Passed |
| API-031 | W14-05 / W15-04 | [test_exchange_tamper_replay_wrong_key_and_expiry](../../backend/tests/test_security.py) | Authentic200; tamper/wrong-key/expiry422; replay409 | Passed |
| API-032 | W14-05 / W15-04 | [test_exchange_unavailable_key](../../backend/tests/test_security.py) | Missing protected key503 | Passed |
| API-033 | W14-05 / W15-04 | [test_last_admin_cannot_be_disabled_and_account_disable_revokes_access](../../backend/tests/test_security.py) | Last-admin disable409; inactive account access401 | Passed |
| API-034 | W13-03 / W15-03 | [test_transient_recovers_and_deduplicates](../../backend/tests/test_worker.py) | Retry then delivered on attempt2; exactly one inbox entry | Passed |
| API-035 | W13-03 / W15-03 | [test_permanent_failure_escalates_without_retry](../../backend/tests/test_worker.py) | Human action on attempt1 with supervisor escalation | Passed |
| API-036 | W13-03 / W15-03 | [test_exhaustion_bounded_and_restart_recovery](../../backend/tests/test_worker.py) | Unavailable event stops at attempt3 and requires action | Passed |
| API-037 | W13-03 / W15-03 | [test_expired_lease_recovers_after_restart](../../backend/tests/test_worker.py) | Live lease held; expired lease resumes delivery on attempt2 | Passed |
| API-038 | W13-03 / W15-03 | [test_missed_detection_not_automatic_absence](../../backend/tests/test_worker.py) | One overdue event and escalation; no inferred absence records | Passed |
| API-039 | W13-03 / W15-03 | [test_provider_timeout_is_bounded](../../backend/tests/test_worker.py) | Slow provider returns within bounded test deadline and queues retry | Passed |
| API-040 | W13-03 / W15-03 | [test_readiness_and_manual_recovery](../../backend/tests/test_worker.py) | No-worker503, fresh-worker200; separate recovery event delivered | Passed |

## Flutter states

[Actual output](../../evidence/week15/flutter-tests.log), [executable cases](../../frontend/test/workflow_test.dart). Each checks WEB-02–04 / W15-01 and the explicit assertion in its source.

| Test ID | Executed scenario | Actual result |
|---|---|---|
| UI-001 | session restoration displays loading state | Passed (final suite) |
| UI-002 | unauthenticated login validates required inputs | Passed (final suite) |
| UI-003 | login opens real client success and empty states | Passed (final suite) |
| UI-004 | network failure can recover using Retry | Passed (final suite) |
| UI-005 | forbidden state is understandable | Passed (final suite) |
| UI-006 | failed save preserves selections and retry idempotency key | Passed (final suite) |
| UI-007 | finalization requires explicit marking and saved changes | Passed (final suite) |
| UI-008 | supervisor attendance has read-only controls | Passed (final suite) |
| UI-009 | overview responsive at width 390.0 | Passed (final suite) |
| UI-010 | overview responsive at width 768.0 | Passed (final suite) |
| UI-011 | overview responsive at width 1440.0 | Passed (final suite) |
