"""Real controlled automation, security, and restoration evidence."""
import json
import secrets
import sqlite3
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import ROOT, Settings
from backend.app.database import Database
from backend.app.domain import enqueue, now
from backend.app.main import create_app
from backend.app.worker import ControlledAdapter, run_once
from scripts.manage import seed
from scripts.metadata import metadata, write_json


def isolated(name):
    destination = ROOT / '.local' / 'exercises' / (name+'-'+secrets.token_hex(4))
    destination.mkdir(parents=True)
    settings = replace(Settings.from_env(), database=str(destination / 'exercise.db'))
    db = Database(settings.database); db.migrate(); seed(db)
    return settings, db


def automation():
    results = []
    for mode in ['normal', 'transient', 'permanent', 'unavailable']:
        settings, db = isolated(mode)
        timestamp = now()
        with db.connect(write=True) as con:
            teacher = con.execute("SELECT id FROM users WHERE role='teacher'").fetchone()[0]
            enqueue(con, 'exercise:'+mode, 1, teacher, 'exercise', 'Controlled fictional delivery', timestamp)
        transitions = []
        for step in range(5):
            transitions.extend(run_once(db, settings, ControlledAdapter(mode), timestamp+step*100))
        with db.connect() as con:
            row = dict(con.execute('SELECT status,attempts,escalated_at FROM notifications WHERE event_id=?', ('exercise:'+mode,)).fetchone())
            delivered = con.execute('SELECT COUNT(*) FROM inbox WHERE event_id=?', ('exercise:'+mode,)).fetchone()[0]
        expected = {'normal': ('delivered', 1), 'transient': ('delivered', 2), 'permanent': ('action_required', 1), 'unavailable': ('action_required', 3)}[mode]
        assert (row['status'], row['attempts']) == expected
        assert delivered <= 1
        results.append({'scenario': mode, 'expected': {'status': expected[0], 'attempts': expected[1]}, 'actual': row, 'inbox_deliveries': delivered, 'result': 'Passed', 'transitions': transitions})
    write_json('evidence/week13/automation.json', {'metadata': metadata('python -m scripts.exercises'), 'clock': 'Controlled clock advanced by 100 seconds between scans; not wall-clock timing', 'results': results})


def security():
    import os
    settings, db = isolated('security')
    client = TestClient(create_app(settings))
    result = client.post('/api/auth/login', json={'username': 'admin', 'password': os.environ['DEMO_ADMIN_PASSWORD']})
    assert result.status_code == 200
    client.headers['X-CSRF-Token'] = result.json()['csrf']
    envelope = client.post('/api/reports/exchange/send').json()
    cases = []
    def check(name, response, expected):
        assert response.status_code == expected, name
        cases.append({'scenario': name, 'expected_status': expected, 'actual_status': response.status_code, 'result': 'Passed'})
    check('invalid credentials', client.post('/api/auth/login', json={'username': 'missing', 'password': 'invalid-test-only'}), 401)
    altered = {**envelope, 'ciphertext': ('B' if envelope['ciphertext'][0] != 'B' else 'A')+envelope['ciphertext'][1:]}
    check('altered ciphertext rejected', client.post('/api/reports/exchange/receive', json=altered), 422)
    check('authentic report accepted', client.post('/api/reports/exchange/receive', json=envelope), 200)
    check('replay rejected', client.post('/api/reports/exchange/receive', json=envelope), 409)
    check('untrusted origin rejected', client.post('/api/auth/logout', headers={'Origin': 'https://untrusted.invalid'}), 403)
    check('wrong CSRF rejected', client.post('/api/auth/logout', headers={'X-CSRF-Token': 'invalid'}), 403)
    check('logout', client.post('/api/auth/logout'), 200)
    check('revoked session rejected', client.get('/api/auth/me'), 401)
    write_json('evidence/week14/security.json', {'metadata': metadata('python -m scripts.exercises'), 'results': cases, 'additional_negative_cases': 'backend/tests/test_security.py: expiry, wrong key, role and object access, safe validation, password preservation', 'transport': 'In-process integration here; TLS verification recorded separately in week16/tls.json. No tokens, keys, passwords or ciphertext retained.'})


def recovery():
    settings, db = isolated('recovery')
    directory = Path(settings.database).parent.resolve()
    assert directory.is_relative_to((ROOT / '.local' / 'exercises').resolve())
    snapshot, restored = directory / 'snapshot.db', directory / 'restored.db'
    with db.connect() as source, sqlite3.connect(snapshot) as target:
        source.backup(target)
        before = source.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    with db.connect(write=True) as con:
        con.execute("UPDATE students SET display_name='Controlled changed value' WHERE id=1")
    with sqlite3.connect(snapshot) as source, sqlite3.connect(restored) as target:
        source.backup(target)
        integrity = target.execute('PRAGMA integrity_check').fetchone()[0]
        count = target.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        name = target.execute('SELECT display_name FROM students WHERE id=1').fetchone()[0]
    restored_app = create_app(replace(settings, database=str(restored)))
    import os
    client = TestClient(restored_app)
    login = client.post('/api/auth/login', json={'username': 'teacher', 'password': os.environ['DEMO_TEACHER_PASSWORD']})
    client.headers['X-CSRF-Token'] = login.json()['csrf']
    detail = client.get('/api/sessions/1').json()
    saved = client.put('/api/sessions/1/attendance', headers={'Idempotency-Key': secrets.token_hex(16)}, json={'version': detail['version'], 'items': [{'student_id': x['student_id'], 'status': 'present'} for x in detail['students']]})
    final = client.post('/api/sessions/1/finalize', headers={'Idempotency-Key': secrets.token_hex(16)}, json={'version': saved.json()['version']})
    assert integrity == 'ok' and count == before == 12 and name != 'Controlled changed value'
    assert saved.status_code == final.status_code == 200
    write_json('evidence/week16/recovery.json', {'metadata': metadata('python -m scripts.exercises'), 'expected': 'Restore a consistent snapshot and complete attendance workflow', 'actual': {'integrity': integrity, 'students_before': before, 'students_restored': count, 'mutation_removed': True, 'save_status': saved.status_code, 'finalize_status': final.status_code}, 'result': 'Passed', 'scope': 'Isolated SQLite restoration; infrastructure rollback remains a documented procedure.'})


if __name__ == '__main__':
    automation(); security(); recovery()
    print(json.dumps({'automation': 'passed', 'security': 'passed', 'restoration': 'passed'}))
