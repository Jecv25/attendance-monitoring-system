# Week 16 Activity 2: Incomplete release tabletop

This is a clearly labeled classroom exercise scenario, not a claim about an actual failed deployment.

Scenario: a release bundle contains frontend files and API source, but omits the migration version, worker startup instructions, secret injection, trusted HTTPS configuration, a tested backup, and the previous build reference.

| Gap | Consequence | Priority / disposition | Evidence required to clear |
|---|---|---|---|
| Migration/schema unspecified | Writes may fail or damage compatibility | Block release | Versioned migration + fresh/upgrade checks |
| Secret handling undocumented | Operators may embed keys or reuse unsafe defaults | Block release | Placeholder example + protected setup + safe scan |
| Worker omitted | Missed submissions receive no unattended attention | Block automation readiness | Worker command, heartbeat, restart test |
| TLS trust not configured | Cookie/transport objectives unproved | Block HTTPS readiness | Valid TLS and certificate-negative test |
| Backup untested | Recovery promise unsupported | Block recovery recommendation | Consistent backup + integrity/workflow restoration |
| Previous artifact not identified | Rollback instructions cannot be reproduced | Conditional blocker | Recorded source/build and compatible database/config |
| Monitoring owner unnamed | Alerts may not receive action | Conditional risk | Role ownership map and detection walkthrough |

Prioritized plan: establish configuration/migration correctness; complete worker/TLS; rehearse restore; verify workflow/regressions; capture workload and monitoring; issue conditional recommendation. A configuration review alone is not execution evidence. Costs include certificate/key management, controlled backup storage and process supervision. The exercise result supports release-review reasoning; actual release status is determined from real artifacts.
