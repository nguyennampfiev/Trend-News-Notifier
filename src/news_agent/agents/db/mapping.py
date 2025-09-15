import sqlite3
from typing import Dict, List


class MappingDB:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        # Subscription ↔ Tag
        self.conn.execute(
            """
        CREATE TABLE IF NOT EXISTS subscription_tags (
            subscription_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (subscription_id, tag_id),
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
        """
        )
        # Trend ↔ Tag
        self.conn.execute(
            """
        CREATE TABLE IF NOT EXISTS trend_tags (
            trend_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (trend_id, tag_id),
            FOREIGN KEY (trend_id) REFERENCES trends(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
        """
        )
        self.conn.commit()

    def link_subscription_tag(self, subscription_id: int, tag_id: int):
        self.conn.execute(
            "INSERT OR IGNORE INTO subscription_tags (subscription_id, tag_id) VALUES (?, ?)",
            (subscription_id, tag_id),
        )
        self.conn.commit()

    def link_trend_tag(self, trend_id: int, tag_id: int):
        self.conn.execute(
            "INSERT OR IGNORE INTO trend_tags (trend_id, tag_id) VALUES (?, ?)",
            (trend_id, tag_id),
        )
        self.conn.commit()

    def get_matching_trends_for_subscription(self, subscription_id: int) -> List[Dict]:
        cursor = self.conn.execute(
            """
        SELECT t.* FROM trends t
        JOIN trend_tags tt ON t.id = tt.trend_id
        JOIN subscription_tags st ON st.tag_id = tt.tag_id
        WHERE st.subscription_id = ?
        """,
            (subscription_id,),
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
