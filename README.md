# Attendance Monitoring System

**Presence** is a Flutter Web attendance application with a FastAPI API, persistent SQLite database and separate monitoring worker. It is a controlled academic prototype for PFEBSIT 002 Weeks 13–18, based on the supplied student module.

Admin manages accounts, learners, classes, teacher assignments, rosters and sessions. Teachers record and finalize attendance in assigned classes. Supervisors review reports and alerts with read-only access. Attendance supports Present, Late, Absent and Excused; unmarked learners remain Pending. Finalized records require a reasoned, audited correction.

## Run on Windows

Prerequisites: Git, Flutter with web support, PowerShell and an internet connection for initial dependencies. Python is installed **inside this checkout** by setup; no global Python installation is required. Use separate terminal windows when running individual processes.

```powershell
git clone https://github.com/Jecv25/attendance-monitoring-system.git
cd attendance-monitoring-system
.\scripts\setup.ps1
.\scripts\run.ps1
```

Open **http://127.0.0.1:8000**. The API serves the compiled Flutter app and `/api/*` from one origin. Usernames are `admin`, `teacher`, `supervisor`. Setup generates independent passwords in the ignored `.env`; open that file locally to obtain them. No default password is published. Do not copy the file into a submission, screenshot or issue.

```powershell
# Stop only the processes recorded by the startup script:
.\scripts\stop.ps1
# Later starts can reuse an unchanged release build:
.\scripts\run.ps1 -SkipBuild
```

The seed is idempotent: one fictional class, twelve learners, one session and three accounts. It preserves existing records and passwords. Re-running setup does not reset attendance. For a fresh demonstration, configure a separate database path and seed it; evaluation already creates an isolated database per run.

## Development and commands

Run from the repository root unless shown otherwise:

```powershell
$taskPython = '.\.tools\python\python.exe'
& $taskPython -m scripts.manage migrate
& $taskPython -m scripts.manage seed
& $taskPython -m scripts.serve
# In a second terminal:
& $taskPython -m backend.app.worker
# Optional Flutter development server in another terminal:
cd frontend
flutter run -d web-server --web-hostname 127.0.0.1 --web-port 7357 --dart-define=API_BASE=http://127.0.0.1:8000/api
```

On Linux/macOS, create a Python 3.13 virtual environment, install `backend/requirements.lock.txt`, and use its `python` for the same module commands. Flutter Web remains the required client. Linux/macOS setup has not been executed in the submitted Windows environment.

## Verification and evidence

```powershell
.\scripts\setup.ps1 -BrowserTests
$taskPython = '.\.tools\python\python.exe'
& $taskPython -m pytest -q
& $taskPython -m ruff check backend scripts
& $taskPython -m scripts.manage openapi
& $taskPython -m scripts.exercises
& $taskPython -m scripts.tls
cd frontend
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
flutter build web --no-web-resources-cdn
cd ..
& $taskPython -m scripts.evaluate
& $taskPython -m scripts.manage backup
```

Evaluation requires Node and Chrome/Edge, or Playwright Chromium installed through `npx playwright install chromium`. `ATTENDANCE_BROWSER` can select an installed browser executable. The evaluator starts and stops its own loopback servers and uses a fresh fictional database. Do not run another instance on ports 8000/8443 during evaluation.

`scripts.exercises` records controlled-clock retry/failure cases and a real isolated SQLite restoration. `scripts.evaluate` performs real browser journeys, predefined ordinary/peak read workloads, explicit-CA TLS checks and an actual worker-process restart. In-process security tests and real HTTPS transport checks are reported separately.

See [completion report](PROJECT_COMPLETION_REPORT.md), [evidence index](EVIDENCE_INDEX.md), [requirements matrix](REQUIREMENTS_TRACEABILITY.md), [documentation index](docs/README.md), and [OpenAPI](docs/api/openapi.json). Preserved original failing tests demonstrate subsequent fixes; they are not the final acceptance results.

## Security and operations

Authentication uses Argon2id passwords, hashed opaque server sessions, HttpOnly cookies, CSRF checks and backend role/object authorization. Nondevelopment settings require Secure cookies. The local HTTP profile is explicitly development-only. Sensitive report exchange uses AES-256-GCM with backend-owned keys, authenticated metadata, expiry and replay rejection. Keys never enter Flutter.

The worker scans every five seconds. Notifications use durable events, deduplication, leases, a two-second delivery timeout and at most three total attempts. Permanent/exhausted failures require human attention and generate supervisor escalation. Delivery is to a **local inbox adapter**, not real email/SMS. Attendance commits do not depend on delivery.

Reports paginate, and totals apply to the displayed page; dashboard scope is the latest 100 accessible sessions. Dates display in Manila time while report date-filter boundaries are UTC days. Rosters are snapshotted when a session is created. See [limitations](docs/known-limitations-and-risks.md) for residual risks and production gaps.

HTTPS evaluation uses a local CA without changing system trust; see [deployment](deployment/README.md). No certificate-validation bypass is used. Preserve `.env`, database backups and TLS files in restricted local storage; never commit them. Protect the host and its backups: the database itself is not encrypted at rest.

## Academic completion boundary

Actual UAT participation/sign-off, peer-team review, student viva, examination and personal reflection require real people. Templates and preparation are included; the repository does not claim those events occurred. The module is the academic source; technical sources and AI assistance are acknowledged in `docs/acknowledgments.md`.
