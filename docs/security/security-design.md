# Security objectives and control selection

Design and review baseline. Evidence of implementation and execution is separate. The application uses fictional data; that does not remove the need to demonstrate access control and safe integration.

| Data / location | Classification and objective | Control and limitation |
|---|---|---|
| Student ID/display name and attendance in database | Minimized educational record; confidentiality, integrity, accountability | Server authorization, constrained writes, minimized audit and local filesystem permissions; SQLite storage is not automatically encrypted |
| Password | Authentication secret | Established Argon2 password hashing; never reversible encryption or a general-purpose fast hash |
| Browser authentication session | Bearer credential | Server-side hashed/opaque session handling, expiration/invalidation, HttpOnly cookie, SameSite, Secure under HTTPS; endpoint compromise remains a risk |
| Authenticated write | Integrity and user intent | CSRF control and appropriate Origin policy in addition to session authentication |
| Report in transit | Confidentiality and endpoint authenticity | HTTPS with certificate validation; localhost HTTP is a documented development exception only |
| Exchanged report payload | Confidentiality and integrity beyond transport | Backend AES-GCM with fresh nonce and authenticated metadata; keys stay outside client/repository |
| Replay identity | Freshness / one accepted message | Persist accepted message ID only with successful verification, enforce expiry and atomic uniqueness; correct clock and retention matter |
| Backup | Contains same record sensitivity | Consistent SQLite backup, restricted storage, restore verification; backup alone is not proof of recoverability |
| Logs/screenshots | Operational diagnostics | Safe IDs, category/state/correlation, redaction and minimal data; never passwords, session/CSRF values, keys or full bodies |

Least privilege applies to operation and object: teachers are limited to assigned classes, supervisors are read-only, and administrator management must not be granted through frontend state. Validate shapes, limits, date ranges, membership, state and stale versions on the server. Reject malformed values safely. Avoid wildcard credentialed CORS and raw exception disclosure. Login throttling is bounded and should be reviewed before distributed deployment.

Source-inspected defaults: one-hour authentication sessions; Argon2id with time cost 2, memory 19,456 KiB and parallelism 1; login limit 8 failures in a 900-second window; report key is 32 base64-configured bytes, active version `v1`; 12-byte random AES-GCM nonce; envelope lifetime at most 300 seconds with 30 seconds permitted future issue-time skew. `backend/app/config.py`, `security.py`, `schemas.py` and the generated contract own the exact settings. Source inspection is distinct from executed verification.

## Report envelope sketch

Sender and receiver are protected backend operations for a minimized attendance report. Use an established AES-GCM implementation. A canonical authenticated metadata representation binds message ID, issue time, expiry, and key version; changing these must invalidate authentication. Generate a fresh random nonce of the library's required size. Treat the ciphertext and tag as opaque transport data. Verify authentication before accepting the payload, then enforce semantic constraints and replay uniqueness transactionally. The receiver returns a minimized verification outcome rather than exposing private keys or full records.

Encryption is reversible confidentiality; password hashing is one-way verification. A MAC authenticates to a shared-secret holder; it does not establish public attribution. Digital signatures can support independent verification but require a separate signing-key lifecycle and are not justified merely because they sound stronger. AES-GCM already authenticates the encrypted envelope; a second ad hoc hash or home-made cipher adds no established protection.

## Key and secret lifecycle

Generate report keys with a cryptographic random source and inject through ignored local environment/configuration. Keep development, tests, and deployment values separate. Do not send keys to Flutter. Version report keys; controlled rotation must decide whether old unexpired messages can still be verified and how old keys are retired. If the implementation supports one active key only, document that rotation invalidates outstanding envelopes instead of claiming transparent historical decryption.

On suspected compromise: disable affected exchange/session usage, rotate the key or credentials, invalidate sessions as appropriate, record the event without secret content, retest, and review access. Back up recoverable configuration separately from committed source with restricted access. Loss of an encryption key means loss of access to the affected encrypted reports; do not promise key recovery from source control.

TLS private keys and local test CA files are runtime configuration. A client must trust the controlled CA explicitly when needed; never use `verify=False` or disabled certificate checks as evidence of HTTPS verification. Browser localhost HTTP checks and trusted TLS API checks establish different things and must be reported separately.

## Retention and residual risks

Proposed classroom retention: fictional attendance for the demonstration period; operational logs short-lived and rotated; audit and backup retention approved by an authorized owner before real use. Source-inspected worker cleanup removes expired authentication sessions and login-attempt windows and idempotency records older than the default 90 days; report receive cleans expired replay identities after an additional skew margin. These validity/retention boundaries must be tested. There is no blanket attendance/audit purge or approved institutional retention policy implied. Repeating an idempotency key after its retention window is not guaranteed to return the historical response.

Risks: compromised endpoints/accounts can act within their privileges; the prototype does not prove physical presence; a single host/database can fail; local notifications do not establish external delivery; SQLite files/backups need host protection; throttling and sessions need distributed design before scaling; clock error affects schedules/expiry; dependency vulnerabilities can emerge; no independent penetration test or production approval is claimed.
