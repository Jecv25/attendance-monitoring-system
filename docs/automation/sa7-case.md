# SA7 automation case and portfolio guide

Problem: an authorized teacher needs dependable confirmation that attendance was saved; operators need evidence that scheduled sessions receive attention even when nobody opens the browser.

Decision: combine a trusted scheduled scan with durable deduplicated notification work. Browser timers cannot meet the unattended requirement. A distributed message broker is a feasible future option but adds operational work outside the single-host prototype boundary.

Normal path: save explicit statuses, review, finalize, report and audit. Adverse paths include invalid input, forbidden class access, provider unavailability, transient recovery, permanent rejection, retry exhaustion, and restart. Separate attendance confirmation from notification delivery so a failed alert cannot undo the record.

Portfolio map: boundary/data flow and screen flow in architecture docs; trigger/failure/retry policy in automation design; protected configuration in security docs; actual requests/logs/results in the evidence index; recovery in deployment runbook; maintainability in `docs/maintenance.md`.

Maintainability evaluation: small domain functions, versioned contract/migrations, controlled clock/failure adapter, finite policy settings, and correlation IDs support change. Costs remain database/process ownership, provider adapter maintenance, dependency review, retention, and evidence regeneration after behavior changes. Conclusions are conditional on actual verification; no production authorization is implied.
