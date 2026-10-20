"""SQLite history. Only complete user/assistant pairs enter conversation memory."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL, model TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
                CREATE INDEX IF NOT EXISTS message_history ON messages(conversation_id, id);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, title='New conversation'):
        identifier = str(uuid4())
        with self.connection() as db:
            db.execute('INSERT INTO conversations(id,title) VALUES (?,?)', (identifier, title))
        return self.get(identifier)

    def list(self):
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                'SELECT * FROM conversations ORDER BY updated_at DESC, rowid DESC')]

    def get(self, identifier):
        with self.connection() as db:
            row = db.execute('SELECT * FROM conversations WHERE id=?', (identifier,)).fetchone()
            if row is None:
                raise KeyError(identifier)
            result = dict(row)
            result['messages'] = [dict(m) for m in db.execute(
                'SELECT * FROM messages WHERE conversation_id=? ORDER BY id', (identifier,))]
            return result

    def delete(self, identifier):
        with self.connection() as db:
            return db.execute('DELETE FROM conversations WHERE id=?', (identifier,)).rowcount > 0

    def save_turn(self, identifier, prompt, answer, model):
        with self.connection() as db:
            db.executemany(
                'INSERT INTO messages(conversation_id,role,content,model) VALUES (?,?,?,?)',
                [(identifier, 'user', prompt, model), (identifier, 'assistant', answer, model)])
            db.execute("""UPDATE conversations SET
                title=CASE WHEN title='New conversation' THEN ? ELSE title END,
                updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?""",
                (' '.join(prompt.split())[:80], identifier))
