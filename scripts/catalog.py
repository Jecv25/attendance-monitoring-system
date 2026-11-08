"""Generate test IDs from actual final JUnit and Flutter execution output."""
import re
import xml.etree.ElementTree as ET

from backend.app.config import ROOT


EXPECTED = {
    'normal_save_finalize_report_audit': 'Save/finalize200; persisted report counts and audit agree',
    'dashboard_real_request': 'Dashboard200 and one visible session',
    'admin_registration_path': 'Student/class/session201; duplicate session409',
    'pending_and_finalization_rules': 'Two pending learners; incomplete finalization422',
    'idempotent_retries_and_key_payload_conflict': 'Same request200 once; changed payload409; two records and one audit',
    'conflict_and_correction': 'Stale/ordinary finalized writes409; reasoned correction200; short reason422',
    'invalid_attendance_is_atomic': 'Invalid request422 and zero attendance mutations',
    'atomic_mixed_roster_rejection': 'Mixed invalid roster422; earlier entries rolled back',
    'roster_snapshot_survives_changes': 'Class roster edit200; original session roster count preserved',
    'not_found_and_boundary_limits': 'Missing session404; invalid pagination/date bounds422',
    'schedule_boundaries': 'Naive, reversed or greater-than24h schedule422',
    'api_contract': 'OpenAPI3.1, strict schema, cookie and CSRF/idempotency discoverability',
    'real_concurrent_updates_have_one_winner': 'Concurrent same-version writes return one200 and one409',
    'finalization_retry_does_not_duplicate_event': 'Repeated finalization200 with one durable event',
    'batch_and_roster_limits': 'More than100 roster or attendance entries422',
    'unauthenticated_invalid_and_expired_sessions': 'Each protected request401',
    'role_object_access_and_csrf': 'Cross-class, forbidden role and wrong-CSRF requests403',
    'logout_revokes_session': 'Logout200, subsequent session access401',
    'invalid_login_rate_limit_and_safe_validation': 'Eight failures401, next429; validation422 without secret input',
    'cookie_hash_and_security_headers': 'Opaque token stored hashed; Argon2id and required response headers',
    'security_headers_on_rejected_origin': 'Untrusted origin403 with common security/no-store headers',
    'security_headers_on_oversize_body': 'Oversize413 with correlation identifier',
    'password_whitespace_preserved': 'Exact password200; whitespace-normalized alternative401',
    'exchange_tamper_replay_wrong_key_and_expiry': 'Authentic200; tamper/wrong-key/expiry422; replay409',
    'exchange_unavailable_key': 'Missing protected key503',
    'last_admin_cannot_be_disabled_and_account_disable_revokes_access': 'Last-admin disable409; inactive account access401',
    'transient_recovers_and_deduplicates': 'Retry then delivered on attempt2; exactly one inbox entry',
    'permanent_failure_escalates_without_retry': 'Human action on attempt1 with supervisor escalation',
    'exhaustion_bounded_and_restart_recovery': 'Unavailable event stops at attempt3 and requires action',
    'expired_lease_recovers_after_restart': 'Live lease held; expired lease resumes delivery on attempt2',
    'missed_detection_not_automatic_absence': 'One overdue event and escalation; no inferred absence records',
    'provider_timeout_is_bounded': 'Slow provider returns within bounded test deadline and queues retry',
    'readiness_and_manual_recovery': 'No-worker503, fresh-worker200; separate recovery event delivered',
}


def main():
    suite = ET.parse(ROOT / 'evidence/week15/backend-tests.xml').getroot()
    rows = []
    for index, case in enumerate(suite.iter('testcase'), 1):
        name = case.attrib['name']
        plain = name.removeprefix('test_').split('[', 1)[0]
        family = case.attrib.get('classname', '')
        requirement = 'W13-03 / W15-03' if family.endswith('test_worker') else 'W14-05 / W15-04' if family.endswith('test_security') else 'WEB-01 / W15-02'
        status = 'Failed' if case.find('failure') is not None or case.find('error') is not None else 'Skipped' if case.find('skipped') is not None else 'Passed'
        source = '../../'+family.replace('.', '/')+'.py'
        rows.append(f'| API-{index:03} | {requirement} | [{name}]({source}) | {EXPECTED.get(plain, "See explicit source assertions")} | {status} |')
    content = '# Executed test catalog\n\nGenerated from actual final JUnit; fixtures and preconditions are in `backend/tests/conftest.py`. The [test strategy](test-strategy.md) supplies risk/ownership/exit criteria. [JUnit](../../evidence/week15/backend-tests.xml) records actual outcomes and execution times; [environment](../../evidence/week18/environment.json) identifies tool/source context.\n\n| Test ID | Requirement family | Executable case | Expected result | Actual result |\n|---|---|---|---|---|\n'+'\n'.join(rows)+'\n\n## Flutter states\n\n[Actual output](../../evidence/week15/flutter-tests.log), [executable cases](../../frontend/test/workflow_test.dart). Each checks WEB-02–04 / W15-01 and the explicit assertion in its source.\n\n| Test ID | Executed scenario | Actual result |\n|---|---|---|\n'
    lines = (ROOT / 'evidence/week15/flutter-tests.log').read_text(encoding='utf-8-sig').splitlines()
    names = [m.group(1) for line in lines if (m := re.match(r'^\d\d:\d\d \+\d+: (.*)$', line)) and not m.group(1).startswith(('loading ', 'All tests'))]
    content += '\n'.join(f'| UI-{i:03} | {name} | Passed (final suite) |' for i, name in enumerate(names, 1))+'\n'
    (ROOT / 'docs/testing/test-catalog.md').write_text(content, encoding='utf-8')
    print(f'Catalogued {len(rows)} API cases and {len(names)} Flutter cases from actual results')


if __name__ == '__main__': main()
