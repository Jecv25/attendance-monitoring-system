"""Local management commands; fictional seed data and safe database backup."""
import argparse
import base64
import json
import os
import secrets
import sqlite3
from pathlib import Path

from backend.app.config import ROOT, Settings
from backend.app.database import Database
from backend.app.domain import now
from backend.app.security import PASSWORDS


def configure():
    path = ROOT / '.env'
    if path.exists():
        print('Existing .env preserved. Demo credentials are in that local file.')
        return
    values = {
        'ATTENDANCE_ENVIRONMENT': 'development', 'ATTENDANCE_DATABASE': '.local/attendance.db',
        'ATTENDANCE_SECURE_COOKIES': 'false',
        'ATTENDANCE_ORIGINS': 'http://127.0.0.1:7357,http://127.0.0.1:8000,https://localhost:8443',
        'ATTENDANCE_REPORT_KEY': base64.b64encode(secrets.token_bytes(32)).decode(), 'ATTENDANCE_KEY_VERSION': 'v1',
        **{f'DEMO_{role.upper()}_PASSWORD': secrets.token_urlsafe(18) for role in ('admin', 'teacher', 'supervisor')},
    }
    path.write_text('\n'.join(f'{key}={value}' for key, value in values.items())+'\n')
    print('Created ignored .env with generated credentials. Read locally; do not share or record it.')


def seed(db):
    with db.connect(write=True) as con:
        for role in ('admin', 'teacher', 'supervisor'):
            password = os.getenv(f'DEMO_{role.upper()}_PASSWORD', '')
            if len(password) < 12:
                raise ValueError(f'Configure DEMO_{role.upper()}_PASSWORD with at least 12 characters')
            con.execute('INSERT OR IGNORE INTO users(username,display_name,password_hash,role,created_at) VALUES (?,?,?,?,?)', (role, 'Demo '+role.title(), PASSWORDS.hash(password), role, now()))
        teacher_id = con.execute("SELECT id FROM users WHERE username='teacher'").fetchone()[0]
        for index in range(1, 13):
            con.execute('INSERT OR IGNORE INTO students(student_code,display_name,created_at) VALUES (?,?,?)', (f'DEMO-{index:03}', f'Learner {index:02}', now()))
        con.execute('INSERT OR IGNORE INTO classes(code,title,teacher_id,created_at) VALUES (?,?,?,?)', ('BSIT-3A', 'Integrative Programming and Technologies 2', teacher_id, now()))
        class_id = con.execute("SELECT id FROM classes WHERE code='BSIT-3A'").fetchone()[0]
        for student in con.execute("SELECT id FROM students WHERE student_code LIKE 'DEMO-%'").fetchall():
            con.execute('INSERT OR IGNORE INTO rosters VALUES (?,?)', (class_id, student[0]))
        if not con.execute('SELECT 1 FROM sessions WHERE class_id=?', (class_id,)).fetchone():
            sid = con.execute('INSERT INTO sessions(class_id,title,starts_at,ends_at,created_at) VALUES (?,?,?,?,?)', (class_id, 'Demonstration attendance', now()-300, now()+3300, now())).lastrowid
            con.execute('INSERT INTO session_students SELECT ?,student_id FROM rosters WHERE class_id=?', (sid, class_id))
    print('Seeded fictional class and 12 learners. Usernames: admin, teacher, supervisor; passwords are configured locally.')


def backup(db, destination):
    destination = Path(destination).resolve()
    permitted = (ROOT / '.local').resolve()
    if not destination.is_relative_to(permitted) or destination == Path(db.path).resolve():
        raise ValueError('Backup destination must be a separate file inside .local')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with db.connect() as source, sqlite3.connect(destination) as target:
        source.backup(target)
        if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Backup integrity check failed')
    print('Consistent SQLite backup verified inside .local')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['configure', 'migrate', 'seed', 'openapi', 'backup'])
    parser.add_argument('--destination', default='.local/backups/attendance.db')
    args = parser.parse_args()
    if args.command == 'configure':
        configure(); return
    settings = Settings.from_env()
    db = Database(settings.database)
    db.migrate()
    if args.command == 'seed':
        seed(db)
    elif args.command == 'openapi':
        from backend.app.main import create_app
        path = ROOT / 'docs' / 'api' / 'openapi.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(create_app(settings).openapi(), indent=2)+'\n')
        print('Generated docs/api/openapi.json')
    elif args.command == 'backup':
        backup(db, args.destination)
    else:
        print('Database migrations applied')


if __name__ == '__main__':
    main()
