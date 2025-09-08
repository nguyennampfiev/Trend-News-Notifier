import sqlite3
from typing import Dict, List

from .db import AbstractTrendDB


class SQLiteTrendDB(AbstractTrendDB):
    """SQLite implementation of AbstractTrendDB"""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    notified BOOLEAN NOT NULL DEFAULT 0
                )
            """
            )
        self.conn.commit()

    def save_trend(self, topic: str, summary: str, url: str, source: str):
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO trends (topic, summary, url, source, notified)
                VALUES (?, ?, ?, ?, 0)
            """,
                (topic, summary, url, source),
            )
        self.conn.commit()

    def get_unsent_trends(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trends WHERE notified = 0")
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        self.conn.commit()
        return [dict(zip(columns, row)) for row in rows]

    def mark_as_sent(self, trend_id: int):
        with self.conn:
            self.conn.execute(
                """
                UPDATE trends
                SET notified = 1
                WHERE id = ?
            """,
                (trend_id,),
            )
        self.conn.commit()

    def get_all_entries(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT topic, url FROM trends")
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        self.conn.commit()
        return [dict(zip(columns, row)) for row in rows]
