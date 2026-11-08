import uuid

import pytest


def headers():
    return {'Idempotency-Key': uuid.uuid4().hex}


def entries(version=0):
    return {'version': version, 'items': [{'student_id': 1, 'status': 'present'}, {'student_id': 2, 'status': 'late'}]}


def test_normal_save_finalize_report_audit(teacher, admin):
    saved = teacher.put('/api/sessions/1/attendance', json=entries(), headers=headers())
    assert saved.status_code == 200
    final = teacher.post('/api/sessions/1/finalize', json={'version': 1}, headers=headers())
    assert final.status_code == 200
    assert teacher.get('/api/sessions/1').json()['finalized_at']
    report = teacher.get('/api/reports').json()
    assert report['totals']['present'] == report['totals']['late'] == 1
    assert any(x['action'] == 'session_finalized' for x in admin.get('/api/audit').json())


def test_dashboard_real_request(teacher):
    result = teacher.get('/api/dashboard')
    assert result.status_code == 200
    assert result.json()['sessions'] == 1


def test_admin_registration_path(admin):
    student = admin.post('/api/students', json={'student_code': 'NEW-01', 'display_name': 'New learner'})
    assert student.status_code == 201
    created = admin.post('/api/classes', json={'code': 'NEW-CLASS', 'title': 'New controlled class', 'teacher_id': 2})
    assert created.status_code == 201
    cid = created.json()['id']
    assert admin.put(f'/api/classes/{cid}/roster', json={'student_ids': [student.json()['id']]}).status_code == 200
    body = {'class_id': cid, 'title': 'New session', 'starts_at': '2026-11-09T09:00:00+08:00', 'ends_at': '2026-11-09T10:00:00+08:00'}
    assert admin.post('/api/sessions', json=body).status_code == 201
    assert admin.post('/api/sessions', json=body).status_code == 409


def test_pending_and_finalization_rules(teacher):
    assert teacher.get('/api/sessions/1').json()['pending_count'] == 2
    assert teacher.post('/api/sessions/1/finalize', json={'version': 0}, headers=headers()).status_code == 422


def test_idempotent_retries_and_key_payload_conflict(teacher, system):
    key = headers()
    first = teacher.put('/api/sessions/1/attendance', json=entries(), headers=key)
    repeated = teacher.put('/api/sessions/1/attendance', json=entries(), headers=key)
    assert first.status_code == repeated.status_code == 200
    assert first.json() == repeated.json()
    changed = entries(); changed['items'][0]['status'] = 'absent'
    assert teacher.put('/api/sessions/1/attendance', json=changed, headers=key).status_code == 409
    with system['db'].connect() as con:
        assert con.execute('SELECT COUNT(*) FROM attendance').fetchone()[0] == 2
        assert con.execute("SELECT COUNT(*) FROM audit WHERE action='attendance_saved'").fetchone()[0] == 1


def test_conflict_and_correction(teacher):
    assert teacher.put('/api/sessions/1/attendance', json=entries(), headers=headers()).status_code == 200
    assert teacher.put('/api/sessions/1/attendance', json=entries(), headers=headers()).status_code == 409
    assert teacher.post('/api/sessions/1/finalize', json={'version': 1}, headers=headers()).status_code == 200
    assert teacher.put('/api/sessions/1/attendance', json=entries(2), headers=headers()).status_code == 409
    correction = {'student_id': 2, 'status': 'excused', 'version': 2, 'reason': 'Approved controlled correction'}
    assert teacher.post('/api/sessions/1/corrections', json=correction, headers=headers()).status_code == 200
    assert teacher.get('/api/sessions/1').json()['counts']['excused'] == 1
    assert teacher.post('/api/sessions/1/corrections', json={**correction, 'reason': 'x'}, headers=headers()).status_code == 422


@pytest.mark.parametrize('payload', [
    {'version': -1, 'items': [{'student_id': 1, 'status': 'present'}]},
    {'version': 0, 'items': []},
    {'version': 0, 'items': [{'student_id': 1, 'status': 'unknown'}]},
    {'version': 0, 'items': [{'student_id': 1, 'status': 'present'}]*2},
    {'version': 0, 'items': [{'student_id': 3, 'status': 'present'}]},
    {'version': 0, 'items': [{'student_id': 1, 'status': 'present'}], 'unexpected': True},
])
def test_invalid_attendance_is_atomic(teacher, system, payload):
    assert teacher.put('/api/sessions/1/attendance', json=payload, headers=headers()).status_code == 422
    with system['db'].connect() as con:
        assert con.execute('SELECT COUNT(*) FROM attendance').fetchone()[0] == 0


def test_atomic_mixed_roster_rejection(teacher, system):
    body = entries(); body['items'].append({'student_id': 3, 'status': 'present'})
    assert teacher.put('/api/sessions/1/attendance', json=body, headers=headers()).status_code == 422
    assert teacher.get('/api/sessions/1').json()['pending_count'] == 2


def test_roster_snapshot_survives_changes(admin, teacher):
    assert admin.put('/api/classes/1/roster', json={'student_ids': [1]}).status_code == 200
    assert teacher.get('/api/sessions/1').json()['roster_count'] == 2


def test_not_found_and_boundary_limits(teacher):
    assert teacher.get('/api/sessions/999999').status_code == 404
    assert teacher.get('/api/students?limit=101').status_code == 422
    assert teacher.get('/api/students?offset=-1').status_code == 422
    assert teacher.get('/api/reports?from_date=2026-12-01&to_date=2026-01-01').status_code == 422
    assert teacher.get('/api/reports?from_date=2024-01-01&to_date=2026-01-01').status_code == 422


@pytest.mark.parametrize('start,end', [('2026-11-09T09:00:00', '2026-11-09T10:00:00'), ('2026-11-09T10:00:00Z','2026-11-09T09:00:00Z'), ('2026-11-09T09:00:00Z','2026-11-11T09:00:00Z')])
def test_schedule_boundaries(admin, start, end):
    assert admin.post('/api/sessions', json={'class_id': 1, 'title': 'Invalid schedule', 'starts_at': start, 'ends_at': end}).status_code == 422


def test_api_contract(admin):
    schema = admin.get('/api/openapi.json').json()
    assert schema['openapi'].startswith('3.1.')
    assert '/api/sessions/{session_id}/attendance' in schema['paths']
    assert schema['components']['schemas']['AttendanceInput']['additionalProperties'] is False
    assert schema['components']['securitySchemes']['CookieSession']['in'] == 'cookie'
    operation = schema['paths']['/api/sessions/{session_id}/attendance']['put']
    assert {'X-CSRF-Token', 'Idempotency-Key'}.issubset({x['name'] for x in operation['parameters']})


def test_real_concurrent_updates_have_one_winner(system):
    from concurrent.futures import ThreadPoolExecutor
    from fastapi.testclient import TestClient
    import threading
    barrier = threading.Barrier(2)
    def submit(status):
        with TestClient(system['app']) as client:
            client.cookies.update(system['clients']['teacher'].cookies)
            client.headers['X-CSRF-Token'] = system['clients']['teacher'].headers['X-CSRF-Token']
            body = entries(); body['items'][0]['status'] = status
            barrier.wait(timeout=5)
            return client.put('/api/sessions/1/attendance', json=body, headers=headers()).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, ['present', 'absent'])) == [200, 409]


def test_finalization_retry_does_not_duplicate_event(teacher, system):
    teacher.put('/api/sessions/1/attendance', json=entries(), headers=headers())
    key = headers()
    first = teacher.post('/api/sessions/1/finalize', json={'version': 1}, headers=key)
    retry = teacher.post('/api/sessions/1/finalize', json={'version': 1}, headers=key)
    assert first.status_code == retry.status_code == 200
    assert first.json() == retry.json()
    with system['db'].connect() as con:
        assert con.execute("SELECT COUNT(*) FROM notifications WHERE event_id='finalized:1'").fetchone()[0] == 1


def test_batch_and_roster_limits(admin, teacher):
    assert admin.put('/api/classes/1/roster', json={'student_ids': list(range(1, 102))}).status_code == 422
    assert teacher.put('/api/sessions/1/attendance', json={'version': 0, 'items': [{'student_id': i, 'status': 'present'} for i in range(1, 102)]}, headers=headers()).status_code == 422
