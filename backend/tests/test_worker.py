import time
from dataclasses import replace

from backend.app.domain import enqueue, now
from backend.app.worker import ControlledAdapter, run_once


def event(system, name='test:event'):
    timestamp = now()
    with system['db'].connect(write=True) as con:
        enqueue(con, name, 1, 2, 'test', 'Fictional controlled notification', timestamp)
    return timestamp


def read(system, name='test:event'):
    with system['db'].connect() as con:
        return dict(con.execute('SELECT * FROM notifications WHERE event_id=?', (name,)).fetchone())


def test_transient_recovers_and_deduplicates(system):
    timestamp = event(system)
    run_once(system['db'], system['settings'], ControlledAdapter('transient'), timestamp)
    assert read(system)['status'] == 'retry'
    run_once(system['db'], system['settings'], ControlledAdapter('transient'), timestamp+10)
    assert read(system)['status'] == 'delivered'
    assert read(system)['attempts'] == 2
    run_once(system['db'], system['settings'], timestamp=timestamp+20)
    assert read(system)['attempts'] == 2
    with system['db'].connect() as con:
        assert con.execute("SELECT COUNT(*) FROM inbox WHERE event_id='test:event'").fetchone()[0] == 1


def test_permanent_failure_escalates_without_retry(system):
    timestamp = event(system)
    run_once(system['db'], system['settings'], ControlledAdapter('permanent'), timestamp)
    item = read(system)
    assert item['status'] == 'action_required' and item['attempts'] == 1 and item['escalated_at']
    with system['db'].connect() as con:
        assert con.execute("SELECT COUNT(*) FROM notifications WHERE kind='escalation'").fetchone()[0] == 1


def test_exhaustion_bounded_and_restart_recovery(system):
    timestamp = event(system)
    for step in range(5):
        run_once(system['db'], system['settings'], ControlledAdapter('unavailable'), timestamp+step*100)
    assert read(system)['attempts'] == 3
    assert read(system)['status'] == 'action_required'


def test_expired_lease_recovers_after_restart(system):
    timestamp = event(system)
    with system['db'].connect(write=True) as con:
        con.execute("UPDATE notifications SET lease_until=?,attempts=1 WHERE event_id='test:event'", (timestamp+30,))
    run_once(system['db'], system['settings'], timestamp=timestamp+10)
    assert read(system)['attempts'] == 1
    run_once(system['db'], system['settings'], timestamp=timestamp+31)
    assert read(system)['status'] == 'delivered' and read(system)['attempts'] == 2


def test_missed_detection_not_automatic_absence(system):
    with system['db'].connect(write=True) as con:
        con.execute('UPDATE sessions SET starts_at=?,ends_at=? WHERE id=1', (now()-6000, now()-4000))
    run_once(system['db'], system['settings'])
    run_once(system['db'], system['settings'])
    with system['db'].connect() as con:
        assert con.execute("SELECT COUNT(*) FROM notifications WHERE event_id='overdue:1'").fetchone()[0] == 1
        assert con.execute("SELECT COUNT(*) FROM notifications WHERE kind='escalation'").fetchone()[0] == 1
        assert con.execute('SELECT COUNT(*) FROM attendance').fetchone()[0] == 0


def test_provider_timeout_is_bounded(system):
    class Slow:
        def deliver(self, db, item):
            time.sleep(.2)
    timestamp = event(system)
    started = time.monotonic()
    run_once(system['db'], replace(system['settings'], notification_timeout=.02), Slow(), timestamp)
    assert time.monotonic()-started < .18
    assert read(system)['status'] == 'retry'


def test_readiness_and_manual_recovery(system, teacher):
    assert teacher.get('/api/health/ready').status_code == 503
    timestamp = event(system)
    run_once(system['db'], system['settings'], ControlledAdapter('permanent'), timestamp)
    assert teacher.get('/api/health/ready').status_code == 200
    alert = read(system)
    assert teacher.post(f'/api/alerts/{alert["id"]}/retry').status_code == 200
    run_once(system['db'], system['settings'], timestamp=timestamp+10)
    with system['db'].connect() as con:
        assert con.execute("SELECT status FROM notifications WHERE kind='recovery'").fetchone()[0] == 'delivered'
