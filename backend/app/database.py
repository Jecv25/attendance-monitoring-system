"""SQLite connections and immutable, numbered SQL migrations."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self, write=False):
        con = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA busy_timeout=10000')
        try:
            if write:
                con.execute('BEGIN IMMEDIATE')
            yield con
            if write:
                con.commit()
        except BaseException:
            if write:
                con.rollback()
            raise
        finally:
            con.close()

    def migrate(self):
        with self.connect() as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY)')
            for file in sorted((Path(__file__).parents[1] / 'migrations').glob('*.sql')):
                if not con.execute('SELECT 1 FROM schema_migrations WHERE version=?', (file.name,)).fetchone():
                    con.executescript('BEGIN IMMEDIATE;\n' + file.read_text() + "\nINSERT INTO schema_migrations VALUES ('" + file.name.replace("'", "''") + "');\nCOMMIT;")
