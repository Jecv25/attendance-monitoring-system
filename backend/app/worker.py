"""Single-process durable schedule monitor and bounded notification delivery."""
import argparse
import json
import logging
import queue
import random
import threading
import time

from .config import Settings
from .database import Database
from .domain import audit, enqueue, now

log = logging.getLogger('attendance.worker')


class PermanentDeliveryError(Exception):
    pass


class LocalInboxAdapter:
    """Fictional-data local delivery, not an email/SMS provider."""

    def deliver(self, db, event):
        with db.connect(write=True) as con:
            con.execute('INSERT OR IGNORE INTO inbox VALUES (?,?,?,?)',
                        (event['event_id'], event['recipient_id'], event['message'], now()))


class ControlledAdapter(LocalInboxAdapter):
    """Test/CLI-only dependency failure injection; never an HTTP control."""

    def __init__(self, mode='normal'):
        self.mode = mode

    def deliver(self, db, event):
        if self.mode == 'permanent':
            raise PermanentDeliveryError('provider_rejected')
        if self.mode == 'unavailable' or (self.mode == 'transient' and event['attempts'] == 1):
            raise TimeoutError('provider_unavailable')
        return super().deliver(db, event)


def bounded_delivery(adapter, db, event, timeout):
    result = queue.Queue(maxsize=1)

    def invoke():
        try:
            adapter.deliver(db, event)
            result.put(None)
        except Exception as exc:
            result.put(exc)

    threading.Thread(target=invoke, daemon=True).start()
    try:
        outcome = result.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError('provider_timeout')
    if outcome is not None:
        raise outcome


def escalate(con, event, timestamp):
    if event['kind'] == 'escalation':
        return
    for supervisor in con.execute("SELECT id FROM users WHERE role='supervisor' AND active=1").fetchall():
        enqueue(con, f'escalation:{event["event_id"]}:{supervisor[0]}', event['session_id'], supervisor[0], 'escalation',
                f'Human review required for notification #{event["id"]}', timestamp)
    con.execute('UPDATE notifications SET escalated_at=COALESCE(escalated_at,?) WHERE id=?', (timestamp, event['id']))


def run_once(db: Database, settings: Settings, adapter=None, timestamp=None):
    adapter = adapter or LocalInboxAdapter()
    timestamp = now() if timestamp is None else timestamp
    with db.connect(write=True) as con:
        con.execute('INSERT OR REPLACE INTO worker_health VALUES (1,?)', (timestamp,))
        con.execute('DELETE FROM auth_sessions WHERE expires_at<?', (timestamp,))
        con.execute('DELETE FROM login_attempts WHERE reset_at<?', (timestamp,))
        con.execute('DELETE FROM idempotency WHERE created_at<?', (timestamp-settings.retention_days*86400,))
        rows = con.execute('SELECT s.*,c.teacher_id FROM sessions s JOIN classes c ON c.id=s.class_id WHERE s.finalized_at IS NULL').fetchall()
        for session in rows:
            sid = session['id']
            if session['starts_at']-settings.reminder_seconds <= timestamp < session['ends_at']:
                enqueue(con, f'reminder:{sid}', sid, session['teacher_id'], 'reminder', f'Attendance session #{sid} is awaiting submission', timestamp)
            if timestamp >= session['ends_at']+settings.overdue_seconds:
                enqueue(con, f'overdue:{sid}', sid, session['teacher_id'], 'overdue', f'Attendance session #{sid} is overdue; review pending entries', timestamp)
            if timestamp >= session['ends_at']+settings.overdue_seconds+settings.escalation_seconds:
                for supervisor in con.execute("SELECT id FROM users WHERE role='supervisor' AND active=1").fetchall():
                    enqueue(con, f'missed:{sid}:{supervisor[0]}', sid, supervisor[0], 'escalation', f'Attendance session #{sid} needs supervisor review', timestamp)
        candidates = con.execute("SELECT * FROM notifications WHERE status IN ('pending','retry') AND next_attempt<=? AND (lease_until IS NULL OR lease_until<=?) ORDER BY id LIMIT 100", (timestamp, timestamp)).fetchall()
        claimed = []
        for row in candidates:
            event = dict(row)
            if event['attempts'] >= 3:
                con.execute("UPDATE notifications SET status='action_required',last_error='interrupted_final_attempt',updated_at=?,lease_until=NULL WHERE id=?", (timestamp, event['id']))
                escalate(con, event, timestamp)
                continue
            event['attempts'] += 1
            con.execute('UPDATE notifications SET attempts=?,lease_until=?,updated_at=? WHERE id=?', (event['attempts'], timestamp+30, timestamp, event['id']))
            claimed.append(event)
    outcomes = []
    for event in claimed:
        try:
            bounded_delivery(adapter, db, event, settings.notification_timeout)
            status, error, next_attempt = 'delivered', None, timestamp
        except PermanentDeliveryError:
            status, error, next_attempt = 'action_required', 'permanent_provider_rejection', timestamp
        except (TimeoutError, ConnectionError, OSError):
            status = 'action_required' if event['attempts'] >= 3 else 'retry'
            error, next_attempt = 'transient_provider_failure', timestamp+min(60, 2**event['attempts'])+random.uniform(0, .25)
        except Exception:
            status, error, next_attempt = 'action_required', 'unclassified_provider_failure', timestamp
        with db.connect(write=True) as con:
            con.execute('UPDATE notifications SET status=?,last_error=?,next_attempt=?,updated_at=?,lease_until=NULL WHERE id=?', (status, error, next_attempt, timestamp, event['id']))
            if status == 'action_required':
                escalate(con, event, timestamp)
            audit(con, None, 'notification_'+status, event['id'], {'attempt': event['attempts'], 'category': error}, event['event_id'])
        outcome = {'event': 'notification_transition', 'correlation_id': event['event_id'], 'notification_id': event['id'], 'attempt': event['attempts'], 'status': status, 'category': error}
        log.info(json.dumps(outcome))
        outcomes.append(outcome)
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    settings = Settings.from_env()
    db = Database(settings.database)
    db.migrate()
    while True:
        run_once(db, settings)
        if args.once:
            break
        time.sleep(5)


if __name__ == '__main__':
    main()
