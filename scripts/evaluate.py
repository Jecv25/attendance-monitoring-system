"""Own and stop local servers while collecting live deployment evidence."""
import json
import argparse
import os
import ssl
import subprocess
import sys
import time

import httpx

from backend.app.config import ROOT, Settings
from backend.app.database import Database
from backend.app.domain import enqueue
from scripts.manage import seed
from scripts.metadata import metadata, write_json


def wait(base, verify=True):
    last_error = None
    for _ in range(60):
        try:
            if httpx.get(base+'/api/health/live', verify=verify, timeout=1).status_code == 200: return
        except httpx.HTTPError as exc:
            last_error = str(exc)
            if 'CERTIFICATE_VERIFY_FAILED' in last_error: raise
        time.sleep(.25)
    raise RuntimeError('Owned evaluation server did not become live: '+str(last_error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-performance', action='store_true')
    args = parser.parse_args()
    Settings.from_env()
    local = ROOT / '.local' / 'evaluation'; local.mkdir(parents=True, exist_ok=True)
    import secrets
    run = local / ('run-'+secrets.token_hex(4)); run.mkdir()
    os.environ['ATTENDANCE_DATABASE'] = str(run / 'attendance.db')
    db = Database(os.environ['ATTENDANCE_DATABASE']); db.migrate(); seed(db)
    processes, files = [], []
    def start(name, args):
        output = (local / (name+'.log')).open('w', encoding='utf-8'); files.append(output)
        process = subprocess.Popen([sys.executable, '-m', *args], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        processes.append(process); return process
    try:
        worker = start('worker', ['backend.app.worker'])
        http = start('http', ['scripts.serve'])
        wait('http://127.0.0.1:8000')
        for _ in range(30):
            if httpx.get('http://127.0.0.1:8000/api/health/ready').status_code == 200: break
            time.sleep(.25)
        health = httpx.get('http://127.0.0.1:8000/api/health/ready')
        assert health.status_code == 200
        if not args.skip_performance:
            subprocess.run([sys.executable, '-m', 'scripts.performance', '--pid', str(http.pid)], cwd=ROOT, check=True)
        browser = subprocess.run(['node', 'scripts/browser.cjs'], cwd=ROOT)
        start('https', ['scripts.serve', '--https', '--port', '8443'])
        ca = ssl.create_default_context(cafile=str(ROOT / '.local/tls/ca.pem'))
        wait('https://localhost:8443', ca)
        with httpx.Client(base_url='https://localhost:8443', verify=ca) as client:
            login = client.post('/api/auth/login', json={'username': 'admin', 'password': os.environ['DEMO_ADMIN_PASSWORD']})
            assert login.status_code == 200
            cookie = login.headers['set-cookie']
            client.headers['X-CSRF-Token'] = login.json()['csrf']
            envelope = client.post('/api/reports/exchange/send')
            verified = client.post('/api/reports/exchange/receive', json=envelope.json())
            assert verified.status_code == 200
            assert 'Secure' in cookie and 'HttpOnly' in cookie
            assert login.headers.get('strict-transport-security')
        untrusted_rejected = False
        try: httpx.get('https://localhost:8443/api/health/live')
        except httpx.ConnectError: untrusted_rejected = True
        assert untrusted_rejected
        write_json('evidence/week16/tls.json', {'metadata': metadata('python -m scripts.evaluate'), 'result': 'Passed', 'trusted_local_ca_validation': True, 'untrusted_certificate_rejected': untrusted_rejected, 'secure_httponly_cookie': True, 'hsts_present': True, 'encrypted_sender_receiver_over_https': verified.status_code, 'scope': 'Actual separate HTTPS process on localhost with explicit CA trust; no browser/system trust modification or public hosting claim'})
        with db.connect() as con:
            previous_heartbeat = con.execute('SELECT heartbeat FROM worker_health WHERE id=1').fetchone()[0]
        previous_pid = worker.pid
        worker.terminate(); worker.wait(timeout=10)
        with db.connect(write=True) as con:
            teacher = con.execute("SELECT id FROM users WHERE role='teacher'").fetchone()[0]
            enqueue(con, 'process-restart-recovery', 1, teacher, 'exercise', 'Controlled restart recovery', time.time())
            con.execute("UPDATE notifications SET attempts=1,lease_until=? WHERE event_id='process-restart-recovery'", (time.time()-1,))
        # A new real worker process reads durable database state.
        worker = start('worker-restarted', ['backend.app.worker'])
        advanced, recovered = False, None
        for _ in range(40):
            assert worker.poll() is None
            with db.connect() as con:
                current_heartbeat = con.execute('SELECT heartbeat FROM worker_health WHERE id=1').fetchone()[0]
                recovered = dict(con.execute("SELECT status,attempts FROM notifications WHERE event_id='process-restart-recovery'").fetchone())
            advanced = current_heartbeat > previous_heartbeat
            if advanced and recovered['status'] == 'delivered': break
            time.sleep(.25)
        assert advanced and recovered == {'status': 'delivered', 'attempts': 2} and worker.pid != previous_pid
        restarted = httpx.get('http://127.0.0.1:8000/api/health/ready')
        assert restarted.status_code == 200
        write_json('evidence/week16/deployment.json', {'metadata': metadata('python -m scripts.evaluate'), 'result': 'Passed', 'development': {'transport': 'HTTP loopback', 'secure_cookies': False, 'port': 8000}, 'evaluation': {'transport': 'HTTPS with validated local CA', 'secure_cookies': True, 'port': 8443}, 'readiness_status': health.status_code, 'worker_actual_process_restart': True, 'heartbeat_advanced': advanced, 'worker_pid_changed': worker.pid != previous_pid, 'persisted_event_recovered': recovered, 'post_restart_readiness_status': restarted.status_code, 'scope': 'Two local processes/configurations on one host, same database; not independent infrastructure'})
        print(json.dumps({'live_deployment': 'passed', 'tls': 'passed', 'worker_process_restart': 'passed'}))
        if browser.returncode: raise RuntimeError('Browser verification failed; original failure evidence preserved; independent TLS/restart checks completed')
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
        for output in files: output.close()


if __name__ == '__main__': main()
