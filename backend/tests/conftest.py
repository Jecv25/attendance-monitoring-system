import base64
import secrets
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.domain import now
from backend.app.main import create_app
from backend.app.security import PASSWORDS


@pytest.fixture
def system(tmp_path):
    settings = replace(Settings(), database=str(tmp_path / 'test.db'), report_key=base64.b64encode(secrets.token_bytes(32)).decode())
    app = create_app(settings)
    password = secrets.token_urlsafe(18)
    db = app.state.db
    with db.connect(write=True) as con:
        encoded = PASSWORDS.hash(password)
        for uid, role in [(1, 'admin'), (2, 'teacher'), (3, 'supervisor'), (4, 'teacher')]:
            con.execute('INSERT INTO users VALUES (?,?,?,?,?,1,?)', (uid, f'user{uid}', f'Fictional {role} {uid}', encoded, role, now()))
        con.executemany('INSERT INTO students VALUES (?,?,?,1,?)', [(i, f'TEST-{i}', f'Learner {i}', now()) for i in range(1, 4)])
        con.executemany('INSERT INTO classes VALUES (?,?,?,?,?)', [(1, 'TEST-A', 'Test class A', 2, now()), (2, 'TEST-B', 'Test class B', 4, now())])
        con.executemany('INSERT INTO rosters VALUES (?,?)', [(1, 1), (1, 2), (2, 3)])
        con.execute('INSERT INTO sessions VALUES (1,1,?,?,?,NULL,0,?)', ('Test attendance', now()+3600, now()+7200, now()))
        con.executemany('INSERT INTO session_students VALUES (1,?)', [(1,), (2,)])
    clients = {}
    for uid, role in [(1, 'admin'), (2, 'teacher'), (3, 'supervisor'), (4, 'other')]:
        client = TestClient(app, raise_server_exceptions=False)
        result = client.post('/api/auth/login', json={'username': f'user{uid}', 'password': password})
        assert result.status_code == 200, result.text
        client.headers['X-CSRF-Token'] = result.json()['csrf']
        clients[role] = client
    yield {'app': app, 'db': db, 'settings': settings, 'clients': clients, 'password': password}
    for client in clients.values():
        client.close()


@pytest.fixture
def teacher(system):
    return system['clients']['teacher']


@pytest.fixture
def admin(system):
    return system['clients']['admin']
