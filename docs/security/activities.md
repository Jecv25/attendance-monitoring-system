# Week 14 activities and secure-exchange review

## Activity 1: Five control-selection cases

| Proposed use | Objective / problem | Corrected design | Operational assumption |
|---|---|---|---|
| Encrypt passwords so admin can recover them | Verify a login; reversible storage exposes credentials | Argon2 password hashing with library-managed salts, reset rather than recover | Password parameters and account recovery need owner review |
| SHA-256 an attendance export and send hash beside it | Detect malicious alteration; attacker can replace both | AES-GCM for confidential authenticated report, or a justified authenticated MAC/signature if confidentiality is unnecessary | Key custody and verifier identity are trusted |
| Put report-decryption key in compiled Flutter | Confidential exchange; public clients cannot hide bundled keys | Backend-only encryption/decryption with authorized endpoints | Backend host and secret injection protected |
| Use HTTPS and accept every certificate | Protect transit and authenticate service; verification disabled defeats identity | Trusted certificate/CA and hostname checks, with explicit local test trust | CA distribution and renewal owned by administrator |
| Sign every UI status message | Public attribution is not a requirement and key complexity is unjustified | Server-authorized API over HTTPS, safe audit for accountable state changes | Session, server and audit permissions remain trusted |

These are reasoned corrections, not observed attack results. Selected controls meet distinct confidentiality, integrity, authenticity, availability and accountability goals; no control guarantees absolute security.

## Activity 2: Secure exchange review record

Use the actual run IDs from the evidence index. Until populated, this is a prepared review procedure rather than a passed security assessment.

| Review | Expected safe outcome | Evidence to attach |
|---|---|---|
| Source/config inspection | No live secrets in repo/client; protected environment example uses placeholders | reviewed source paths and sanitized scan output |
| Transport | Trusted TLS succeeds; untrusted/wrong certificate fails validation | client/server configuration and actual test results |
| Valid report | Authorized sender and receiver accept one fresh minimized report | redacted request shape and minimized result |
| Altered ciphertext/tag/metadata | Rejected without plaintext or keys | test ID/status and safe diagnostic category |
| Wrong key | Authentication fails safely | test result, not key bytes |
| Expired/replayed envelope | Rejected with persisted replay state | test result and state observation |
| Invalid/expired authentication | Login required; no sensitive data returned | backend/API tests |
| Wrong role or teacher class | Forbidden; state unchanged | tests and safe audit |
| Logging | No passwords/tokens/keys/unnecessary personal data | sanitized logs + source inspection |

Observed integration results: `evidence/week14/security.json` records 8 passing cases: invalid credentials 401, altered ciphertext 422, authentic report 200, replay 409, untrusted Origin 403, wrong CSRF 403, logout 200, revoked session 401. These use in-process FastAPI integration. The final 40-test backend suite additionally covers expired/altered sessions, wrong key, expired message, role/class access, safe validation and password semantics. `evidence/week16/tls.json` separately verifies actual HTTPS with explicit local CA trust, default untrusted-certificate rejection and secure sender/receiver exchange. Do not conflate in-process checks with transport verification.

Findings format: ID, observation, risk, evidence, owner, proposed disposition, actual fix, original-case rerun, regression result, residual limitation. Actual before/after defects are in `docs/testing/hardening-record.md`. Source/evidence redaction removes incidental test credential values without changing assertions; final staged-publication audit remains necessary. Distinguish control-design review from executed verification and independent assurance.
