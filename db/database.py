import sqlite3
from config import DB_PATH


class TranscriptionDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    language TEXT,
                    duration_seconds REAL,
                    model TEXT DEFAULT 'whisper-large-v3-turbo',
                    tokens INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at
                ON transcriptions(created_at)
            """)
            # Migration: add tokens column if it doesn't exist yet
            try:
                conn.execute("ALTER TABLE transcriptions ADD COLUMN tokens INTEGER DEFAULT 0")
            except Exception:
                pass
            # Backfill tokens for existing records that have 0
            rows = conn.execute("SELECT id, text FROM transcriptions WHERE tokens = 0").fetchall()
            for row_id, text in rows:
                conn.execute("UPDATE transcriptions SET tokens = ? WHERE id = ?",
                             (max(1, len(text) // 4), row_id))

    def insert(self, text: str, language: str = None, duration_seconds: float = None, model: str = "whisper-large-v3-turbo") -> int:
        tokens = max(1, len(text) // 4)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO transcriptions (text, language, duration_seconds, model, tokens) VALUES (?, ?, ?, ?, ?)",
                (text, language, duration_seconds, model, tokens),
            )
            return cursor.lastrowid

    def get_recent(self, limit: int = 20) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM transcriptions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def search(self, query: str, limit: int = 20) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM transcriptions WHERE text LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{query}%", limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM transcriptions").fetchone()[0]

    def get_total_tokens(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COALESCE(SUM(tokens), 0) FROM transcriptions").fetchone()[0]
