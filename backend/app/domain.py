import json
import time
from datetime import datetime, timezone

from fastapi import HTTPException


def now():
    return time.time()


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def audit(con, actor, action, target, detail, correlation='worker'):
    con.execute('INSERT INTO audit(actor_id,action,target,detail,correlation_id,created_at) VALUES (?,?,?,?,?,?)',
                (actor, action, str(target), json.dumps(detail, separators=(',', ':')), correlation, now()))


def visible_class(con, actor, class_id):
    row = con.execute('SELECT c.*,u.display_name teacher_name FROM classes c JOIN users u ON c.teacher_id=u.id WHERE c.id=?', (class_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Class not found')
    if actor['role'] == 'teacher' and row['teacher_id'] != actor['id']:
        raise HTTPException(403, 'This class is not assigned to you')
    return dict(row)


def visible_session(con, actor, session_id):
    row = con.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Session not found')
    visible_class(con, actor, row['class_id'])
    return dict(row)


def session_view(con, row):
    item = dict(row)
    for key in ['starts_at', 'ends_at', 'finalized_at', 'created_at']:
        if key in item:
            item[key] = iso(item[key])
    counts = {x['status']: x['n'] for x in con.execute('SELECT status,COUNT(*) n FROM attendance WHERE session_id=? GROUP BY status', (row['id'],))}
    item['counts'] = counts
    item['roster_count'] = con.execute('SELECT COUNT(*) FROM session_students WHERE session_id=?', (row['id'],)).fetchone()[0]
    item['pending_count'] = item['roster_count'] - sum(counts.values())
    return item


def enqueue(con, event, session_id, recipient, kind, message, timestamp=None):
    timestamp = now() if timestamp is None else timestamp
    con.execute('INSERT OR IGNORE INTO notifications(event_id,session_id,recipient_id,kind,message,next_attempt,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
                (event, session_id, recipient, kind, message, timestamp, timestamp, timestamp))
