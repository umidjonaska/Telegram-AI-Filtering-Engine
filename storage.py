import hashlib
import re
import sqlite3
import time


def text_hash(text: str) -> str:
    """Bir xil e'lon turli guruhlarda kelsa ham bir xil hash beradi"""
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


class Storage:
    """Ko'rilgan xabarlar va AI natijalarini saqlaydi (qayta ishga tushganda ham)"""

    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS seen_messages (
                chat_id INTEGER NOT NULL,
                msg_id  INTEGER NOT NULL,
                seen_at INTEGER NOT NULL,
                PRIMARY KEY (chat_id, msg_id)
            );
            CREATE TABLE IF NOT EXISTS texts (
                hash       TEXT PRIMARY KEY,
                important  INTEGER NOT NULL,
                forwarded  INTEGER NOT NULL DEFAULT 0,
                checked_at INTEGER NOT NULL
            );
            """
        )
        self.db.commit()

    def mark_seen(self, chat_id: int, msg_id: int) -> bool:
        """Yangi bo'lsa True qaytaradi"""
        cur = self.db.execute(
            "INSERT OR IGNORE INTO seen_messages VALUES (?, ?, ?)",
            (chat_id, msg_id, int(time.time())),
        )
        self.db.commit()
        return cur.rowcount == 1

    def get_verdict(self, h: str) -> tuple[bool, bool] | None:
        """(important, forwarded) yoki None"""
        row = self.db.execute("SELECT important, forwarded FROM texts WHERE hash = ?", (h,)).fetchone()
        return (bool(row[0]), bool(row[1])) if row else None

    def save_verdict(self, h: str, important: bool):
        self.db.execute(
            "INSERT OR REPLACE INTO texts (hash, important, forwarded, checked_at) "
            "VALUES (?, ?, COALESCE((SELECT forwarded FROM texts WHERE hash = ?), 0), ?)",
            (h, int(important), h, int(time.time())),
        )
        self.db.commit()

    def mark_forwarded(self, h: str):
        self.db.execute("UPDATE texts SET forwarded = 1 WHERE hash = ?", (h,))
        self.db.commit()

    def cleanup(self, days: int = 30):
        border = int(time.time()) - days * 86400
        self.db.execute("DELETE FROM seen_messages WHERE seen_at < ?", (border,))
        self.db.execute("DELETE FROM texts WHERE checked_at < ?", (border,))
        self.db.commit()

    def close(self):
        self.db.close()
