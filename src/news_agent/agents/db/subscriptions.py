import sqlite3
from typing import Dict, List


class SQLiteSubcriptionDB:
    """SQLite implementation for managing subscriptions"""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    topics TEXT NOT NULL
                )
            """
            )
        self.conn.commit()

    def add_subscription(self, email: str, topics: List[str]):
        topics_str = ",".join(topics)  # Store topics as a comma-separated string
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO subscriptions (email, topics)
                VALUES (?, ?)
            """,
                (email, topics_str),
            )
        self.conn.commit()

    def get_all_subscriptions(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM subscriptions")
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        self.conn.commit()
        return [dict(zip(columns, row)) for row in rows]

    def get_subscribers_for_topic(self, topic: str) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT email, topics FROM subscriptions")
        rows = cursor.fetchall()
        subscribers = []
        for row in rows:
            email, topics_str = row
            topics = topics_str.split(",")
            if topic in topics:
                subscribers.append(email)
        self.conn.commit()
        return subscribers
