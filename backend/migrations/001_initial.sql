CREATE TABLE users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
 display_name TEXT NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','teacher','supervisor')),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)), created_at REAL NOT NULL
);
CREATE TABLE auth_sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
 csrf TEXT NOT NULL, expires_at REAL NOT NULL
);
CREATE INDEX auth_sessions_expiry ON auth_sessions(expires_at);
CREATE TABLE login_attempts (fingerprint TEXT PRIMARY KEY, failures INTEGER NOT NULL, reset_at REAL NOT NULL);
CREATE TABLE students (
 id INTEGER PRIMARY KEY, student_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
 display_name TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at REAL NOT NULL
);
CREATE TABLE classes (
 id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE COLLATE NOCASE, title TEXT NOT NULL,
 teacher_id INTEGER NOT NULL REFERENCES users(id), created_at REAL NOT NULL
);
CREATE TABLE rosters (
 class_id INTEGER NOT NULL REFERENCES classes(id), student_id INTEGER NOT NULL REFERENCES students(id),
 PRIMARY KEY(class_id,student_id)
);
CREATE TABLE sessions (
 id INTEGER PRIMARY KEY, class_id INTEGER NOT NULL REFERENCES classes(id),
 title TEXT NOT NULL, starts_at REAL NOT NULL, ends_at REAL NOT NULL,
 finalized_at REAL, version INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL,
 UNIQUE(class_id,starts_at), CHECK(ends_at>starts_at)
);
CREATE INDEX sessions_schedule ON sessions(ends_at,finalized_at);
CREATE TABLE session_students (
 session_id INTEGER NOT NULL REFERENCES sessions(id), student_id INTEGER NOT NULL REFERENCES students(id),
 PRIMARY KEY(session_id,student_id)
);
CREATE TABLE attendance (
 session_id INTEGER NOT NULL, student_id INTEGER NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('present','late','absent','excused')),
 updated_at REAL NOT NULL, updated_by INTEGER NOT NULL REFERENCES users(id),
 PRIMARY KEY(session_id,student_id),
 FOREIGN KEY(session_id,student_id) REFERENCES session_students(session_id,student_id)
);
CREATE TABLE idempotency (
 actor_id INTEGER NOT NULL REFERENCES users(id), scope TEXT NOT NULL, key TEXT NOT NULL,
 request_hash TEXT NOT NULL, response_json TEXT NOT NULL, created_at REAL NOT NULL,
 PRIMARY KEY(actor_id,scope,key)
);
CREATE TABLE audit (
 id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
 target TEXT NOT NULL, detail TEXT NOT NULL, correlation_id TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE notifications (
 id INTEGER PRIMARY KEY, event_id TEXT NOT NULL UNIQUE,
 session_id INTEGER REFERENCES sessions(id), recipient_id INTEGER NOT NULL REFERENCES users(id),
 kind TEXT NOT NULL, message TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','retry','delivered','action_required')),
 attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL,
 created_at REAL NOT NULL, updated_at REAL NOT NULL, escalated_at REAL,
 lease_until REAL, last_error TEXT
);
CREATE INDEX notifications_due ON notifications(status,next_attempt);
CREATE TABLE inbox (
 event_id TEXT PRIMARY KEY, recipient_id INTEGER NOT NULL REFERENCES users(id),
 message TEXT NOT NULL, delivered_at REAL NOT NULL
);
CREATE TABLE replays (message_id TEXT PRIMARY KEY, expires_at REAL NOT NULL);
CREATE TABLE worker_health (id INTEGER PRIMARY KEY CHECK(id=1), heartbeat REAL NOT NULL);
