import secrets
from dataclasses import replace

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.security import digest


def test_unauthenticated_invalid_and_expired_sessions(system):
    client = TestClient(system['app'])
    assert client.get('/api/students').status_code == 401
    client.cookies.set('attendance_session', 'altered-value')
    assert client.get('/api/students').status_code == 401
    teacher = system['clients']['teacher']
    with system['db'].connect(write=True) as con:
        con.execute('UPDATE auth_sessions SET expires_at=0 WHERE token_hash=?', (digest(teacher.cookies.get('attendance_session')),))
    assert teacher.get('/api/students').status_code == 401


def test_role_object_access_and_csrf(system):
    teacher, supervisor = system['clients']['teacher'], system['clients']['supervisor']
    assert teacher.get('/api/classes/2/roster').status_code == 403
    assert system['clients']['other'].get('/api/sessions/1').status_code == 403
    assert supervisor.post('/api/students', json={'student_code': 'X1', 'display_name': 'X learner'}).status_code == 403
    assert teacher.post('/api/classes', json={'code': 'X1', 'title': 'Other class', 'teacher_id': 2}).status_code == 403
    assert teacher.get('/api/metrics').status_code == 403
    assert teacher.post('/api/auth/logout', headers={'X-CSRF-Token': 'invalid'}).status_code == 403


def test_logout_revokes_session(teacher):
    assert teacher.post('/api/auth/logout').status_code == 200
    assert teacher.get('/api/auth/me').status_code == 401


def test_invalid_login_rate_limit_and_safe_validation(system):
    client = TestClient(system['app'])
    body = {'username': 'missing', 'password': 'fictional-invalid'}
    for _ in range(8):
        assert client.post('/api/auth/login', json=body).status_code == 401
    assert client.post('/api/auth/login', json=body).status_code == 429
    secret = secrets.token_urlsafe(30)
    result = client.post('/api/auth/login', json={'username': 'x', 'password': secret})
    assert result.status_code == 422
    assert secret not in result.text and 'input' not in result.text


def test_cookie_hash_and_security_headers(teacher, system):
    response = teacher.get('/api/auth/me')
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['cache-control'] == 'no-store'
    assert len(response.headers['x-correlation-id']) == 32
    with system['db'].connect() as con:
        token = teacher.cookies.get('attendance_session')
        assert con.execute('SELECT 1 FROM auth_sessions WHERE token_hash=?', (token,)).fetchone() is None
        assert con.execute('SELECT 1 FROM auth_sessions WHERE token_hash=?', (digest(token),)).fetchone()
        assert con.execute('SELECT password_hash FROM users LIMIT 1').fetchone()[0].startswith('$argon2id$')


def test_security_headers_on_rejected_origin(teacher):
    response = teacher.post('/api/auth/logout', headers={'Origin': 'https://untrusted.invalid'})
    assert response.status_code == 403
    assert response.headers.get('x-content-type-options') == 'nosniff'
    assert response.headers.get('cache-control') == 'no-store'


def test_security_headers_on_oversize_body(teacher):
    response = teacher.post('/api/auth/logout', content='x'*250001)
    assert response.status_code == 413
    assert response.headers.get('x-correlation-id')


def test_password_whitespace_preserved(admin, system):
    value = ' '+secrets.token_urlsafe(18)+' '
    created = admin.post('/api/users', json={'username': 'spaceuser', 'display_name': 'Space user', 'password': value, 'role': 'teacher'})
    assert created.status_code == 201
    client = TestClient(system['app'])
    assert client.post('/api/auth/login', json={'username': 'spaceuser', 'password': value}).status_code == 200
    normalized_attempt = client.post('/api/auth/login', json={'username': 'spaceuser', 'password': value.strip()})
    assert normalized_attempt.status_code == 401


def test_exchange_tamper_replay_wrong_key_and_expiry(admin, system, monkeypatch):
    sent = admin.post('/api/reports/exchange/send')
    assert sent.status_code == 200
    envelope = sent.json()
    altered = {**envelope, 'ciphertext': ('A' if envelope['ciphertext'][0] != 'A' else 'B')+envelope['ciphertext'][1:]}
    assert admin.post('/api/reports/exchange/receive', json=altered).status_code == 422
    assert admin.post('/api/reports/exchange/receive', json=envelope).status_code == 200
    assert admin.post('/api/reports/exchange/receive', json=envelope).status_code == 409
    wrong_settings = replace(system['settings'], report_key='A'*43+'=')
    wrong = TestClient(create_app(wrong_settings))
    wrong.cookies.update(admin.cookies)
    wrong.headers.update({'X-CSRF-Token': admin.headers['X-CSRF-Token']})
    assert wrong.post('/api/reports/exchange/receive', json=envelope).status_code == 422
    import backend.app.main as module
    monkeypatch.setattr(module, 'now', lambda: envelope['expires_at']+1)
    assert admin.post('/api/reports/exchange/receive', json=envelope).status_code == 422


def test_exchange_unavailable_key(system):
    client = TestClient(create_app(replace(system['settings'], report_key='')))
    client.cookies.update(system['clients']['admin'].cookies)
    client.headers['X-CSRF-Token'] = system['clients']['admin'].headers['X-CSRF-Token']
    assert client.post('/api/reports/exchange/send').status_code == 503


def test_last_admin_cannot_be_disabled_and_account_disable_revokes_access(admin, system):
    assert admin.put('/api/users/1', json={'display_name': 'Fictional admin', 'role': 'admin', 'active': False}).status_code == 409
    with system['db'].connect(write=True) as con:
        con.execute('UPDATE users SET active=0 WHERE id=2')
    assert system['clients']['teacher'].get('/api/students').status_code == 401
