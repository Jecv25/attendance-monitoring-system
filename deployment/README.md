# Controlled deployment

The application is a single-instance academic prototype. Build Flutter and serve its assets through the API for one origin. Start the separate worker against the same SQLite database. Keep all listeners on loopback unless an authorized maintainer provisions a trusted reverse proxy and controls ingress.

```powershell
.\scripts\setup.ps1 -BrowserTests
.\scripts\run.ps1
# Stop before switching profiles:
.\scripts\stop.ps1
.\scripts\run.ps1 -Https -SkipBuild
```

HTTPS evaluation uses an ephemeral local CA and certificate created by `python -m scripts.tls`; no system trust change is performed. Python clients explicitly trust `.local/tls/ca.pem`. A browser requires explicit trust of that CA or an independently trusted certificate. Never bypass certificate validation. Local certificates expire after seven days; regenerate through a reviewed rotation procedure. Nondevelopment settings fail startup when secure cookies are disabled.

Live, reproducible checks: `python -m scripts.evaluate`. This creates a fresh fictional database per run, owns HTTP, HTTPS and worker processes, collects performance/browser/TLS results and stops those processes. Requires a built Flutter client, Node, Playwright and Chrome/Edge (or installed Playwright Chromium). Browser environment can be set with `ATTENDANCE_BROWSER`.

Recovery procedure: stop owned writers, use SQLite's consistent backup API (`python -m scripts.manage backup`), restore to a separate checked path, run migrations, verify integrity, restore the last compatible application artifact, then verify health and a full attendance workflow. Do not downgrade schema without a separately tested compatibility plan. See `evidence/week16/recovery.json` for the actual isolated restore rehearsal.

No cloud hosting, independent-server availability, real message provider or production authorization is claimed. See `docs/deployment/` for thresholds, tabletop review, release checklist and rollback decisions.
