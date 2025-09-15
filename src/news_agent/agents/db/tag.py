import sqlite3
from typing import Dict, List


class TagDB:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
            )
        """
        )
        self.conn.commit()

    def add_tag(self, name: str) -> int:
        cursor = self.conn.execute(
            "INSERT or IGNORE INTO tags (name) VALUES (?)", (name,)
        )
        self.conn.commit()
        if cursor.lastrowid:
            return cursor.lastrowid
        cursor = self.conn.execute("SELECT id FROM tags WHERE name = ?", (name,))
        return cursor.fetchone()[0]

    def get_all_tags(self) -> List[Dict]:
        cursor = self.conn.execute("SELECT * FROM tags")
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
