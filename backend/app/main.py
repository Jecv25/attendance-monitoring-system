"""Versioned API with authorization and transactional attendance operations."""
import base64
import hashlib
import json
import logging
import re
import secrets
import sqlite3
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import schemas as s
from .config import ROOT, Settings
from .database import Database
from .domain import audit, enqueue, iso, now, session_view, visible_class, visible_session
from .security import DUMMY_HASH, PASSWORDS, digest, verify_password

log = logging.getLogger('attendance')


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    db = Database(settings.database)
    db.migrate()
    app = FastAPI(title='Attendance Monitoring System', version='1.0.0',
                  description='Controlled academic prototype. Cookie authentication; X-CSRF-Token required on authenticated writes.',
                  docs_url='/api/docs', openapi_url='/api/openapi.json', redoc_url=None)
    app.state.db, app.state.settings = db, settings
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.origins), allow_credentials=True,
                       allow_methods=['GET', 'POST', 'PUT', 'PATCH'], allow_headers=['Content-Type', 'X-CSRF-Token', 'Idempotency-Key'])

    @app.middleware('http')
    async def boundary(request: Request, call_next):
        started = time.perf_counter()
        request.state.correlation_id = uuid.uuid4().hex
        response = None
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            if origin and origin not in settings.origins:
                response = JSONResponse({'detail': 'Origin not permitted'}, status_code=403)
            if response is None:
                chunks, size = [], 0
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 250000:
                        response = JSONResponse({'detail': 'Request body too large'}, status_code=413)
                        break
                    chunks.append(chunk)
                request._body = b''.join(chunks)
        if response is None:
            try:
                response = await call_next(request)
            except Exception:
                log.error(json.dumps({'event': 'unhandled_error', 'correlation_id': request.state.correlation_id}))
                response = JSONResponse({'detail': 'Service could not complete this request', 'correlation_id': request.state.correlation_id}, status_code=500)
        response.headers.update({
            'X-Correlation-ID': request.state.correlation_id,
            'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
            'Referrer-Policy': 'no-referrer', 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'",
        })
        if request.url.path.startswith('/api'):
            response.headers['Cache-Control'] = 'no-store'
        if settings.secure_cookies:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        log.info(json.dumps({'event': 'http_request', 'method': request.method, 'path': request.url.path,
                             'status': response.status_code, 'duration_ms': round((time.perf_counter()-started)*1000, 2),
                             'correlation_id': request.state.correlation_id}))
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [{'field': '.'.join(map(str, x['loc'])), 'message': x['msg'], 'type': x['type']} for x in exc.errors()]
        return JSONResponse({'detail': 'Please check the submitted fields', 'errors': errors}, status_code=422)

    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_error(request, exc):
        return JSONResponse({'detail': 'A duplicate or conflicting record exists'}, status_code=409)

    @app.exception_handler(sqlite3.OperationalError)
    async def database_error(request, exc):
        return JSONResponse({'detail': 'Database temporarily unavailable; retry safely'}, status_code=503)

    def actor(request: Request):
        token = request.cookies.get('attendance_session', '')
        if not token or len(token) > 128:
            raise HTTPException(401, 'Sign in to continue')
        with db.connect() as con:
            row = con.execute('SELECT u.id,u.username,u.display_name,u.role,a.csrf FROM auth_sessions a JOIN users u ON u.id=a.user_id WHERE a.token_hash=? AND a.expires_at>? AND u.active=1', (digest(token), now())).fetchone()
        if not row:
            raise HTTPException(401, 'Your session is invalid or expired; sign in again')
        result = dict(row)
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and not secrets.compare_digest(request.headers.get('x-csrf-token', ''), result['csrf']):
            raise HTTPException(403, 'Security check failed; refresh your session')
        return result

    Actor = Annotated[dict, Depends(actor)]

    def admin(user):
        if user['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')

    def writer(user):
        if user['role'] == 'supervisor':
            raise HTTPException(403, 'Your role has read-only access')

    def teacher_exists(con, user_id):
        if not con.execute("SELECT 1 FROM users WHERE id=? AND role='teacher' AND active=1", (user_id,)).fetchone():
            raise HTTPException(422, 'Select an active teacher')

    def require_version(row, version):
        if row['version'] != version:
            raise HTTPException(409, 'This session changed. Reload and review before saving again')

    def idem(con, user, request, scope, body):
        key = request.headers.get('idempotency-key', '')
        if not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', key):
            raise HTTPException(422, 'Supply an Idempotency-Key of 8–100 safe characters')
        fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        old = con.execute('SELECT * FROM idempotency WHERE actor_id=? AND scope=? AND key=?', (user['id'], scope, key)).fetchone()
        if old and old['request_hash'] != fingerprint:
            raise HTTPException(409, 'Idempotency key was used with a different request')
        return key, fingerprint, json.loads(old['response_json']) if old else None

    def remember(con, user, scope, key, fingerprint, result):
        con.execute('INSERT INTO idempotency VALUES (?,?,?,?,?,?)', (user['id'], scope, key, fingerprint, json.dumps(result), now()))

    @app.get('/api/health/live', tags=['Health'])
    def live():
        return {'status': 'alive', 'version': app.version}

    @app.get('/api/health/ready', tags=['Health'])
    def ready(response: Response):
        with db.connect() as con:
            con.execute('SELECT 1').fetchone()
            heartbeat = con.execute('SELECT heartbeat FROM worker_health WHERE id=1').fetchone()
        fresh = bool(heartbeat and now()-heartbeat[0] < settings.worker_stale_seconds)
        response.status_code = 200 if fresh else 503
        return {'database': 'ready', 'worker': 'ready' if fresh else 'stale_or_not_started', 'ready': fresh}

    @app.post('/api/auth/login', tags=['Authentication'])
    def login(body: s.Login, request: Request, response: Response):
        # Persistent per-source+username limit; no password or raw session token is logged.
        fingerprint = digest((request.client.host if request.client else 'local') + ':' + body.username.lower())
        with db.connect(write=True) as con:
            timestamp = now()
            attempt = con.execute('SELECT * FROM login_attempts WHERE fingerprint=?', (fingerprint,)).fetchone()
            if attempt and attempt['reset_at'] > timestamp and attempt['failures'] >= settings.login_limit:
                raise HTTPException(429, 'Too many attempts; try again later', headers={'Retry-After': str(settings.login_window)})
            row = con.execute('SELECT * FROM users WHERE username=?', (body.username,)).fetchone()
            valid = verify_password(row['password_hash'] if row else DUMMY_HASH, body.password)
            if not valid or not row or not row['active']:
                failures = (attempt['failures'] if attempt and attempt['reset_at'] > timestamp else 0) + 1
                con.execute('INSERT OR REPLACE INTO login_attempts VALUES (?,?,?)', (fingerprint, failures, timestamp+settings.login_window))
                # Return instead of raising: preserve the rate-limit transaction.
                return JSONResponse({'detail': 'Invalid username or password'}, status_code=401)
            con.execute('DELETE FROM login_attempts WHERE fingerprint=?', (fingerprint,))
            old_token = request.cookies.get('attendance_session')
            if old_token:
                con.execute('DELETE FROM auth_sessions WHERE token_hash=?', (digest(old_token),))
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            con.execute('INSERT INTO auth_sessions VALUES (?,?,?,?)', (digest(token), row['id'], csrf, timestamp+settings.session_seconds))
            audit(con, row['id'], 'login', 'session', {}, request.state.correlation_id)
            response.set_cookie('attendance_session', token, max_age=settings.session_seconds, httponly=True,
                                secure=settings.secure_cookies, samesite='lax', path='/')
            return {'id': row['id'], 'username': row['username'], 'display_name': row['display_name'], 'role': row['role'], 'csrf': csrf}

    @app.get('/api/auth/me', tags=['Authentication'])
    def me(user: Actor):
        return user

    @app.post('/api/auth/logout', tags=['Authentication'])
    def logout(request: Request, response: Response, user: Actor):
        with db.connect(write=True) as con:
            con.execute('DELETE FROM auth_sessions WHERE token_hash=?', (digest(request.cookies['attendance_session']),))
            audit(con, user['id'], 'logout', 'session', {}, request.state.correlation_id)
        response.delete_cookie('attendance_session', path='/', secure=settings.secure_cookies, httponly=True, samesite='lax')
        return {'message': 'Signed out'}

    @app.get('/api/users', tags=['Administration'])
    def users(user: Actor, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)):
        admin(user)
        with db.connect() as con:
            return [dict(x) for x in con.execute('SELECT id,username,display_name,role,active FROM users ORDER BY id LIMIT ? OFFSET ?', (limit, offset))]

    @app.post('/api/users', status_code=201, tags=['Administration'])
    def add_user(body: s.UserCreate, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            uid = con.execute('INSERT INTO users(username,display_name,password_hash,role,created_at) VALUES (?,?,?,?,?)', (body.username, body.display_name, PASSWORDS.hash(body.password), body.role, now())).lastrowid
            audit(con, user['id'], 'user_created', uid, {'role': body.role}, request.state.correlation_id)
        return {'id': uid}

    @app.put('/api/users/{user_id}', tags=['Administration'])
    def edit_user(user_id: int, body: s.UserUpdate, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            old = con.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            if not old:
                raise HTTPException(404, 'User not found')
            if old['role'] == 'admin' and (body.role != 'admin' or not body.active) and con.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND active=1").fetchone()[0] <= 1:
                raise HTTPException(409, 'Keep at least one active administrator')
            if (body.role != 'teacher' or not body.active) and con.execute('SELECT 1 FROM classes WHERE teacher_id=?', (user_id,)).fetchone():
                raise HTTPException(409, 'Reassign this teacher’s classes first')
            con.execute('UPDATE users SET display_name=?,role=?,active=? WHERE id=?', (body.display_name, body.role, body.active, user_id))
            con.execute('DELETE FROM auth_sessions WHERE user_id=?', (user_id,))
            audit(con, user['id'], 'user_updated', user_id, {'role': body.role, 'active': body.active}, request.state.correlation_id)
        return {'message': 'User updated; existing sessions invalidated'}

    @app.post('/api/users/{user_id}/password', tags=['Administration'])
    def reset_password(user_id: int, body: s.PasswordReset, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            if not con.execute('UPDATE users SET password_hash=? WHERE id=?', (PASSWORDS.hash(body.password), user_id)).rowcount:
                raise HTTPException(404, 'User not found')
            con.execute('DELETE FROM auth_sessions WHERE user_id=?', (user_id,))
            audit(con, user['id'], 'password_reset', user_id, {}, request.state.correlation_id)
        return {'message': 'Password reset; existing sessions invalidated'}

    @app.get('/api/students', tags=['Students'])
    def students(user: Actor, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)):
        with db.connect() as con:
            if user['role'] == 'teacher':
                return [dict(x) for x in con.execute('SELECT DISTINCT s.* FROM students s JOIN rosters r ON s.id=r.student_id JOIN classes c ON c.id=r.class_id WHERE c.teacher_id=? ORDER BY s.student_code LIMIT ? OFFSET ?', (user['id'], limit, offset))]
            return [dict(x) for x in con.execute('SELECT * FROM students ORDER BY student_code LIMIT ? OFFSET ?', (limit, offset))]

    @app.post('/api/students', status_code=201, tags=['Students'])
    def add_student(body: s.StudentInput, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            sid = con.execute('INSERT INTO students(student_code,display_name,active,created_at) VALUES (?,?,?,?)', (body.student_code, body.display_name, body.active, now())).lastrowid
            audit(con, user['id'], 'student_created', sid, {}, request.state.correlation_id)
        return {'id': sid}

    @app.put('/api/students/{student_id}', tags=['Students'])
    def edit_student(student_id: int, body: s.StudentInput, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            if not con.execute('UPDATE students SET student_code=?,display_name=?,active=? WHERE id=?', (body.student_code, body.display_name, body.active, student_id)).rowcount:
                raise HTTPException(404, 'Student not found')
            audit(con, user['id'], 'student_updated', student_id, {'active': body.active}, request.state.correlation_id)
        return {'message': 'Student updated'}

    @app.get('/api/classes', tags=['Classes'])
    def classes(user: Actor, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)):
        with db.connect() as con:
            where, args = ('WHERE c.teacher_id=?', [user['id']]) if user['role'] == 'teacher' else ('', [])
            return [dict(x) for x in con.execute(f'SELECT c.*,u.display_name teacher_name,(SELECT COUNT(*) FROM rosters r WHERE r.class_id=c.id) roster_count FROM classes c JOIN users u ON u.id=c.teacher_id {where} ORDER BY c.code LIMIT ? OFFSET ?', (*args, limit, offset))]

    @app.post('/api/classes', status_code=201, tags=['Classes'])
    def add_class(body: s.ClassInput, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            teacher_exists(con, body.teacher_id)
            cid = con.execute('INSERT INTO classes(code,title,teacher_id,created_at) VALUES (?,?,?,?)', (body.code, body.title, body.teacher_id, now())).lastrowid
            audit(con, user['id'], 'class_created', cid, {'teacher_id': body.teacher_id}, request.state.correlation_id)
        return {'id': cid}

    @app.put('/api/classes/{class_id}', tags=['Classes'])
    def edit_class(class_id: int, body: s.ClassInput, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            visible_class(con, user, class_id)
            teacher_exists(con, body.teacher_id)
            con.execute('UPDATE classes SET code=?,title=?,teacher_id=? WHERE id=?', (body.code, body.title, body.teacher_id, class_id))
            audit(con, user['id'], 'class_updated', class_id, {'teacher_id': body.teacher_id}, request.state.correlation_id)
        return {'message': 'Class updated'}

    @app.get('/api/classes/{class_id}/roster', tags=['Classes'])
    def roster(class_id: int, user: Actor):
        with db.connect() as con:
            visible_class(con, user, class_id)
            return [dict(x) for x in con.execute('SELECT s.* FROM students s JOIN rosters r ON r.student_id=s.id WHERE r.class_id=? ORDER BY s.student_code', (class_id,))]

    @app.put('/api/classes/{class_id}/roster', tags=['Classes'])
    def set_roster(class_id: int, body: s.RosterInput, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            visible_class(con, user, class_id)
            for sid in body.student_ids:
                if not con.execute('SELECT 1 FROM students WHERE id=? AND active=1', (sid,)).fetchone():
                    raise HTTPException(422, 'Roster must contain active students')
            con.execute('DELETE FROM rosters WHERE class_id=?', (class_id,))
            con.executemany('INSERT INTO rosters VALUES (?,?)', [(class_id, sid) for sid in body.student_ids])
            audit(con, user['id'], 'roster_updated', class_id, {'count': len(body.student_ids)}, request.state.correlation_id)
        return {'message': 'Roster updated; existing session snapshots preserved'}

    def session_query(con, user, limit=100, offset=0, class_id=None, from_date=None, to_date=None):
        filters, args = [], []
        if user['role'] == 'teacher':
            filters.append('c.teacher_id=?'); args.append(user['id'])
        if class_id is not None:
            visible_class(con, user, class_id)
            filters.append('c.id=?'); args.append(class_id)
        if from_date and to_date and (to_date < from_date or (to_date-from_date).days > 366):
            raise HTTPException(422, 'Date range must be ordered and at most 366 days')
        if from_date:
            filters.append('s.starts_at>=?'); args.append(datetime.combine(from_date, datetime.min.time(), timezone.utc).timestamp())
        if to_date:
            filters.append('s.starts_at<?'); args.append(datetime.combine(to_date+timedelta(days=1), datetime.min.time(), timezone.utc).timestamp())
        where = 'WHERE ' + ' AND '.join(filters) if filters else ''
        return con.execute(f'SELECT s.*,c.code class_code,c.title class_title,u.display_name teacher_name FROM sessions s JOIN classes c ON c.id=s.class_id JOIN users u ON u.id=c.teacher_id {where} ORDER BY s.starts_at DESC,s.id DESC LIMIT ? OFFSET ?', (*args, limit, offset)).fetchall()

    @app.get('/api/sessions', tags=['Attendance'])
    def sessions(user: Actor, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), class_id: int | None = Query(None, gt=0)):
        with db.connect() as con:
            return [session_view(con, x) for x in session_query(con, user, limit, offset, class_id)]

    @app.post('/api/sessions', status_code=201, tags=['Attendance'])
    def add_session(body: s.SessionInput, request: Request, user: Actor):
        admin(user)
        with db.connect(write=True) as con:
            visible_class(con, user, body.class_id)
            if not con.execute('SELECT 1 FROM rosters WHERE class_id=?', (body.class_id,)).fetchone():
                raise HTTPException(422, 'Add a roster before creating a session')
            sid = con.execute('INSERT INTO sessions(class_id,title,starts_at,ends_at,created_at) VALUES (?,?,?,?,?)', (body.class_id, body.title, body.starts_at.timestamp(), body.ends_at.timestamp(), now())).lastrowid
            con.execute('INSERT INTO session_students SELECT ?,student_id FROM rosters WHERE class_id=?', (sid, body.class_id))
            audit(con, user['id'], 'session_created', sid, {'class_id': body.class_id}, request.state.correlation_id)
        return {'id': sid}

    @app.get('/api/sessions/{session_id}', tags=['Attendance'])
    def session_detail(session_id: int, user: Actor):
        with db.connect() as con:
            row = visible_session(con, user, session_id)
            result = session_view(con, row)
            result['class_code'] = visible_class(con, user, row['class_id'])['code']
            result['students'] = [dict(x) for x in con.execute('SELECT st.id student_id,st.student_code,st.display_name,a.status FROM session_students ss JOIN students st ON st.id=ss.student_id LEFT JOIN attendance a ON a.session_id=ss.session_id AND a.student_id=ss.student_id WHERE ss.session_id=? ORDER BY st.student_code', (session_id,))]
            return result

    @app.put('/api/sessions/{session_id}/attendance', tags=['Attendance'])
    def save_attendance(session_id: int, body: s.AttendanceInput, request: Request, user: Actor):
        writer(user)
        scope = f'attendance:{session_id}'
        with db.connect(write=True) as con:
            row = visible_session(con, user, session_id)
            key, fingerprint, previous = idem(con, user, request, scope, body)
            if previous is not None:
                return previous
            require_version(row, body.version)
            if row['finalized_at']:
                raise HTTPException(409, 'Use a reasoned correction for finalized attendance')
            for item in body.items:
                if not con.execute('SELECT 1 FROM session_students WHERE session_id=? AND student_id=?', (session_id, item.student_id)).fetchone():
                    raise HTTPException(422, 'Student is not in this session roster')
                con.execute('INSERT INTO attendance VALUES (?,?,?,?,?) ON CONFLICT(session_id,student_id) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at,updated_by=excluded.updated_by', (session_id, item.student_id, item.status, now(), user['id']))
            con.execute('UPDATE sessions SET version=version+1 WHERE id=?', (session_id,))
            result = {'message': 'Attendance saved', 'version': row['version']+1}
            remember(con, user, scope, key, fingerprint, result)
            audit(con, user['id'], 'attendance_saved', session_id, {'entries': len(body.items)}, request.state.correlation_id)
        return result

    @app.post('/api/sessions/{session_id}/finalize', tags=['Attendance'])
    def finalize(session_id: int, body: s.VersionInput, request: Request, user: Actor):
        writer(user)
        scope = f'finalize:{session_id}'
        with db.connect(write=True) as con:
            row = visible_session(con, user, session_id)
            key, fingerprint, previous = idem(con, user, request, scope, body)
            if previous is not None:
                return previous
            require_version(row, body.version)
            if row['finalized_at']:
                raise HTTPException(409, 'Session is already finalized')
            counts = session_view(con, row)
            if counts['pending_count'] or not counts['roster_count']:
                raise HTTPException(422, 'Explicitly mark every student before finalizing')
            timestamp = now()
            con.execute('UPDATE sessions SET finalized_at=?,version=version+1 WHERE id=?', (timestamp, session_id))
            teacher = visible_class(con, user, row['class_id'])['teacher_id']
            enqueue(con, f'finalized:{session_id}', session_id, teacher, 'finalized', f'Attendance session #{session_id} was finalized', timestamp)
            result = {'message': 'Session finalized', 'version': row['version']+1, 'finalized_at': iso(timestamp)}
            remember(con, user, scope, key, fingerprint, result)
            audit(con, user['id'], 'session_finalized', session_id, {}, request.state.correlation_id)
        return result

    @app.post('/api/sessions/{session_id}/corrections', tags=['Attendance'])
    def correction(session_id: int, body: s.CorrectionInput, request: Request, user: Actor):
        writer(user)
        scope = f'correction:{session_id}'
        with db.connect(write=True) as con:
            row = visible_session(con, user, session_id)
            key, fingerprint, previous = idem(con, user, request, scope, body)
            if previous is not None:
                return previous
            require_version(row, body.version)
            if not row['finalized_at']:
                raise HTTPException(409, 'Use attendance entry before finalization')
            old = con.execute('SELECT status FROM attendance WHERE session_id=? AND student_id=?', (session_id, body.student_id)).fetchone()
            if not old:
                raise HTTPException(422, 'Student is not in finalized attendance')
            con.execute('UPDATE attendance SET status=?,updated_at=?,updated_by=? WHERE session_id=? AND student_id=?', (body.status, now(), user['id'], session_id, body.student_id))
            con.execute('UPDATE sessions SET version=version+1 WHERE id=?', (session_id,))
            audit(con, user['id'], 'attendance_corrected', session_id, {'student_id': body.student_id, 'from': old[0], 'to': body.status, 'reason': body.reason}, request.state.correlation_id)
            result = {'message': 'Correction recorded', 'version': row['version']+1}
            remember(con, user, scope, key, fingerprint, result)
        return result

    def build_report(user, from_date=None, to_date=None, class_id=None, limit=100, offset=0):
        with db.connect() as con:
            rows = [session_view(con, x) for x in session_query(con, user, limit, offset, class_id, from_date, to_date)]
            return {'sessions': rows, 'totals': {status: sum(x['counts'].get(status, 0) for x in rows) for status in ('present', 'late', 'absent', 'excused')}, 'scope': 'Displayed page; session dates filtered by UTC day', 'limit': limit, 'offset': offset}

    @app.get('/api/reports', tags=['Reports'])
    def reports(user: Actor, from_date: date | None = None, to_date: date | None = None, class_id: int | None = Query(None, gt=0), limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)):
        return build_report(user, from_date, to_date, class_id, limit, offset)

    @app.get('/api/dashboard', tags=['Reports'])
    def dashboard(user: Actor):
        report = build_report(user)
        rows = report['sessions']
        return {'sessions': len(rows), 'finalized': sum(bool(x['finalized_at']) for x in rows), 'pending_students': sum(x['pending_count'] for x in rows), 'totals': report['totals'], 'recent_sessions': rows[:5], 'scope': 'Latest 100 sessions'}

    @app.get('/api/alerts', tags=['Monitoring'])
    def alerts(user: Actor, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)):
        with db.connect() as con:
            where, args = ('WHERE n.recipient_id=? OR c.teacher_id=?', [user['id'], user['id']]) if user['role'] == 'teacher' else ('', [])
            return [dict(x) for x in con.execute(f'SELECT n.id,n.event_id,n.session_id,n.kind,n.message,n.status,n.attempts,n.created_at,n.updated_at,n.last_error,n.escalated_at,u.display_name recipient FROM notifications n JOIN users u ON u.id=n.recipient_id LEFT JOIN sessions s ON s.id=n.session_id LEFT JOIN classes c ON c.id=s.class_id {where} ORDER BY n.created_at DESC LIMIT ? OFFSET ?', (*args, limit, offset))]

    @app.post('/api/alerts/{alert_id}/retry', tags=['Monitoring'])
    def recover_alert(alert_id: int, request: Request, user: Actor):
        writer(user)
        with db.connect(write=True) as con:
            row = con.execute('SELECT * FROM notifications WHERE id=?', (alert_id,)).fetchone()
            if not row:
                raise HTTPException(404, 'Alert not found')
            if row['session_id']:
                visible_session(con, user, row['session_id'])
            elif row['recipient_id'] != user['id'] and user['role'] != 'admin':
                raise HTTPException(403, 'This alert is not assigned to you')
            if row['status'] != 'action_required':
                raise HTTPException(409, 'Only failed alerts can be queued for manual recovery')
            event = f'recovery:{row["event_id"]}:{row["id"]}'
            enqueue(con, event, row['session_id'], row['recipient_id'], 'recovery', row['message'])
            audit(con, user['id'], 'alert_recovery_requested', alert_id, {'new_event': event}, request.state.correlation_id)
        return {'message': 'Recovery queued as a separate bounded delivery'}

    @app.get('/api/audit', tags=['Audit'])
    def audit_list(user: Actor, limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0)):
        with db.connect() as con:
            where, args = ('WHERE a.actor_id=?', [user['id']]) if user['role'] == 'teacher' else ('', [])
            return [dict(x) for x in con.execute(f'SELECT a.*,u.display_name actor FROM audit a LEFT JOIN users u ON u.id=a.actor_id {where} ORDER BY a.id DESC LIMIT ? OFFSET ?', (*args, limit, offset))]

    @app.get('/api/metrics', tags=['Monitoring'])
    def metrics(user: Actor):
        if user['role'] == 'teacher':
            raise HTTPException(403, 'Operational metrics require oversight access')
        with db.connect() as con:
            counts = {x['status']: x['n'] for x in con.execute('SELECT status,COUNT(*) n FROM notifications GROUP BY status')}
            return {'notifications': counts, 'attempts': con.execute('SELECT COALESCE(SUM(attempts),0) FROM notifications').fetchone()[0], 'delivery': 'local inbox adapter; not email or SMS'}

    def report_key():
        try:
            key = base64.b64decode(settings.report_key, validate=True)
            if len(key) != 32:
                raise ValueError()
            return key
        except (ValueError, TypeError):
            raise HTTPException(503, 'Protected report exchange is not configured')

    @app.post('/api/reports/exchange/send', tags=['Secure exchange'])
    def send_report(request: Request, user: Actor):
        admin(user)
        metadata = {'message_id': uuid.uuid4().hex, 'issued_at': int(now()), 'expires_at': int(now())+300, 'key_version': settings.key_version}
        payload = build_report(user)
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(report_key()).encrypt(nonce, json.dumps(payload, separators=(',', ':')).encode(), json.dumps(metadata, sort_keys=True).encode())
        with db.connect(write=True) as con:
            audit(con, user['id'], 'report_encrypted', metadata['message_id'], {'key_version': settings.key_version}, request.state.correlation_id)
        return {**metadata, 'nonce': base64.b64encode(nonce).decode(), 'ciphertext': base64.b64encode(ciphertext).decode()}

    @app.post('/api/reports/exchange/receive', tags=['Secure exchange'])
    def receive_report(body: s.Envelope, request: Request, user: Actor):
        admin(user)
        if body.key_version != settings.key_version:
            raise HTTPException(422, 'Report envelope could not be verified')
        metadata = body.model_dump(exclude={'nonce', 'ciphertext'})
        try:
            nonce = base64.b64decode(body.nonce, validate=True)
            if len(nonce) != 12:
                raise ValueError()
            plaintext = AESGCM(report_key()).decrypt(nonce, base64.b64decode(body.ciphertext, validate=True), json.dumps(metadata, sort_keys=True).encode())
            payload = json.loads(plaintext)
        except (InvalidTag, ValueError, TypeError):
            raise HTTPException(422, 'Report envelope could not be verified')
        timestamp = now()
        if body.issued_at > timestamp+30 or body.expires_at <= timestamp or not 0 < body.expires_at-body.issued_at <= 300:
            raise HTTPException(422, 'Report envelope is expired or has invalid timing')
        with db.connect(write=True) as con:
            con.execute('DELETE FROM replays WHERE expires_at<?', (timestamp-30,))
            if con.execute('SELECT 1 FROM replays WHERE message_id=?', (body.message_id,)).fetchone():
                raise HTTPException(409, 'Report envelope was already received')
            con.execute('INSERT INTO replays VALUES (?,?)', (body.message_id, body.expires_at))
            audit(con, user['id'], 'report_verified', body.message_id, {}, request.state.correlation_id)
        return {'verified': True, 'message_id': body.message_id, 'session_count': len(payload.get('sessions', []))}

    frontend = ROOT / 'frontend' / 'build' / 'web'
    def documented_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        schema.setdefault('components', {}).setdefault('securitySchemes', {})['CookieSession'] = {'type': 'apiKey', 'in': 'cookie', 'name': 'attendance_session', 'description': 'HttpOnly server-managed session. Obtain via /api/auth/login.'}
        for path, operations in schema['paths'].items():
            for method, operation in operations.items():
                if method not in ('get', 'post', 'put', 'patch', 'delete'):
                    continue
                if '/health/' in path or path == '/api/auth/login':
                    continue
                operation['security'] = [{'CookieSession': []}]
                if method != 'get':
                    operation.setdefault('parameters', []).append({'name': 'X-CSRF-Token', 'in': 'header', 'required': True, 'schema': {'type': 'string'}, 'description': 'In-memory CSRF value returned by login or /auth/me.'})
                if path.endswith(('/attendance', '/finalize', '/corrections')) and method != 'get':
                    operation.setdefault('parameters', []).append({'name': 'Idempotency-Key', 'in': 'header', 'required': True, 'schema': {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{8,100}$'}, 'description': 'Reuse unchanged on a retry; use a new key for a different operation.'})
        app.openapi_schema = schema
        return schema
    app.openapi = documented_openapi
    if (frontend / 'index.html').exists():
        app.mount('/', StaticFiles(directory=Path(frontend), html=True), name='flutter-web')
    return app
