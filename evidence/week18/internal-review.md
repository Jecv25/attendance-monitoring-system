# Internal pre-defense review

This is a developer review of this project's artifacts, not the module's actual review of another team's work.

| Observed gap | Disposition / evidence |
|---|---|
| Dashboard/report route helper received framework parameter objects | Fixed pure reporting helper; original failures and40-test regression retained. |
| Early rejection bypassed common security headers | Fixed shared decoration/logging;403/413 cases retested. |
| Password normalization accepted a modified credential | Preserve exact password input; rejected normalized variant retested. Synthetic credential redacted from original output. |
| Sidebar Material/width exceptions | Correct Material ancestor and bounded brand;11 Flutter tests now pass. |
| Browser semantics/focus and offscreen controls | Persist accessibility semantics, use real key events/scroll and awaited response synchronization;8 browser checks pass. Original harness failures remain separate. |
| Strict TLS rejected incomplete certificate metadata | Added key identifiers/usages; trusted-CA success and untrusted rejection verified without disabling validation. |
| Fresh old heartbeat could hide a failed restart | Require a new PID, advancing heartbeat and actual persisted-event delivery; deployment JSON confirms all three. |
| UAT/peer/viva could be confused with generated documents | Explicit pending human participation throughout portfolio. |

Fallback: real screenshots, JUnit, structured events, workload measurements and restoration/restart records linked from the root evidence index. Preflight and the timed demonstration plan are in `docs/defense/demo.md`. Student rehearsal and independent assessment still require real participation.
