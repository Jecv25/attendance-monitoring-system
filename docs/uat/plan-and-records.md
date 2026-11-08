# Controlled UAT plan and records

Status: **Pending Human Participation**. This package prepares representative-role testing; no participant feedback, acceptance, signature, or instructor approval is asserted. Developer walkthroughs belong in technical evidence, not this independent UAT result record.

Scope: one bounded fictional attendance workflow and relevant adverse/recovery behavior in the final build. Participants: an Admin representative, an assigned Teacher representative, and a Supervisor representative. One person may exercise more than one controlled role if explicitly recorded; do not describe that as independent representation without qualification. Authorized acceptance decision maker: designated course/stakeholder reviewer, to be identified by the actual session organizer.

Preparation: record build, environment, browser/width, controlled dataset, date/time and participant role. Reset fictional data using the documented procedure. Explain the task and expected business outcome without coaching clicks or suggesting a pass. Record observations exactly, distinguish usability findings from defects/change requests, and never collect real student records.

Separate actual developer browser checks are recorded in `developer-verification.md` (8 passing checks,0 page errors). They establish technical support only and do not populate the participant result/acceptance fields below.

| ID | Role / precondition | Steps and controlled data | Measurable acceptance / expected result | Evidence |
|---|---|---|---|---|
| UAT-01 | Admin signed in | Create fictional class, teacher assignment, 5-student roster, valid session | Records appear once and remain after refresh; invalid end-before-start rejected | Observation + relevant screenshot/API reference |
| UAT-02 | Assigned Teacher | Open session; mark 5 explicit statuses; save; refresh | Saved statuses match all five entries; no duplicate student/session records | Saved-state and report observation |
| UAT-03 | Teacher, one Pending | Attempt finalization, mark final student, review, confirm | Pending blocks finalization; complete roster finalizes and ordinary edits are blocked | Safe messages and resulting state |
| UAT-04 | Authorized Teacher | Correct one finalized status with reason; attempt blank reason | Valid correction appears in report/audit; blank reason rejected | Reason/audit observation without secrets |
| UAT-05 | Supervisor | Open summary/report/audit; attempt modification through available workflow | Required review data visible; no modifying action authorized | Role navigation + denied API reference if exercised |
| UAT-06 | Other Teacher | Attempt to access class not assigned to account | No other-class roster or attendance disclosed; state unchanged | Safe denied result |
| UAT-07 | Teacher with unsaved entries | Controlled service interruption during save, then recover and retry | Failure is clear; entries retained; only confirmed save is shown as saved; no duplicate | Before/after observation |
| UAT-08 | Teacher/Supervisor | Inspect controlled overdue session and alert | Pending attendance is distinguished from Absent; owner/escalation understood | Alert and pending-state observation |
| UAT-09 | Teacher, narrow browser | Complete main task at 390 px width and with keyboard | Labels/status/actions readable and reachable; no essential action clipped | Actual viewport and keyboard observation |
| UAT-10 | Authorized reviewer | Compare attendance report with finalized controlled session | Totals agree with explicit statuses and selected scope | Report comparison |

## Activity 1: Replace vague acceptance

| Vague statement | Measurable criterion | Authority | Evidence |
|---|---|---|---|
| “Attendance saves properly” | Five explicit roster statuses persist after reload, with one record each and matching report | Teacher representative + reviewer | UAT-02 and integrity test |
| “The app is secure” | Supervisor cannot write and Teacher cannot view other-class data in controlled cases | Authorized reviewer | UAT-05/06 + separate security tests; residual risks retained |
| “It works on phones” | Core browser task remains readable/operable at stated 390 px width | Teacher representative | UAT-09; no claim of native mobile build |
| “Alerts are reliable” | Controlled overdue session has one owned logical alert and pending attendance is unchanged | Supervisor representative | UAT-08 + worker failure tests |
| “Recovery is easy” | After controlled save failure, entries remain and retry yields one confirmed result | Teacher representative | UAT-07 and idempotency test |

## Actual session record — leave pending until performed

- Session ID / build / environment / date/time: Pending.
- Actual participant name or approved anonymized identifier and represented role: Pending.
- Authorized decision maker: Pending.
- Scenario actual observations, expected-versus-actual result and artifact: Pending.
- Finding ID, severity (blocking/major/minor/change request), evidence: Pending.
- Disposition (fix/accept/defer/out of scope), decision maker and reason: Pending.
- Approved fix, source reference, original-case retest and regression: Pending.
- Participant acknowledgment/acceptance or rejection: Pending.

Do not pre-fill “passed” or invent quotes/signatures. Acceptance can be conditional; unresolved limitations and authority must be explicit. Retain original findings even after fixes.
