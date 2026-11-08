# Developer browser verification record

This is **developer technical verification**, not independent UAT, participant testimony or stakeholder acceptance. Actual UAT scenarios,findings,dispositions and signatures remain pending in `plan-and-records.md`.

Actual artifact: `evidence/week18/browser/results.json`. Execution2026-11-08 14:52:41 UTC (22:52:41 Asia/Manila),Chrome148.0.7778.179,command `node scripts/browser.cjs`,fictional seeded class and12 learners. Result:8 checks passed,0 captured page errors.

| Actual scenario | Observed outcome | Supporting artifact |
|---|---|---|
| Required-field validation | Passed | Results JSON and login screenshot |
| Teacher login → roster → save → finalize | Passed; save200,finalize200 | `03-attendance-saved.png`, `04-attendance-finalized.png` |
| Persisted report and audit history | Passed | `05-reports-desktop.png`, `06-audit-desktop.png` |
| Unavailable service and retry recovery | Passed | `07-unavailable-service.png` and resumed journey |
| Tablet width768 | Passed as visual capture; no-layout-exception assertions are separate widget tests | `08-dashboard-768.png`, `09-sessions-768.png` |
| Narrow width390 | Passed as visual capture; separate widget checks | `08-dashboard-390.png`, `09-sessions-390.png` |
| Keyboard focus | Passed bounded focus check | Results JSON; not a full screen-reader/WCAG audit |
| Anonymous API access | Expected401,actual401,Passed | Results JSON |

Desktop1440,tablet768 and narrow390 captures were inspected. Source also has11 passing widget/state tests at390/768/1440 and40 backend cases. Backend Admin registration and role/class authorization tests provide separate technical support; the browser record does not assert every role's entire interface was independently exercised by people.

Original `failure.json`, `attempt2-failure.json`, screenshots and semantics diagnostic are preserved. Locator/input synchronization issues are distinct from an actual authentication rejection. The app keeps a lifetime accessibility semantics handle; the harness uses real keyboard input,scrolling and synchronized actions. The final passing artifact supersedes the harness failures without erasing them.

These records can inform the UAT facilitator but must not be copied into the participant observation/sign-off fields as if a real teacher or supervisor supplied them. Participants should perform the prepared scenarios without coaching and record their own findings.
