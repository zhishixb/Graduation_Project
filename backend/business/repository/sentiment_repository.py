import sqlite3
from pathlib import Path
from typing import Optional, Dict

class SentimentRepository:
    def __init__(self, db_path: Path):
        self._db_path = db_path

    def get_by_major(self, major: str) -> Optional[Dict[str, object]]:
        query = """
            SELECT weighted_pos_total, weighted_neg_total,
                   total_likes, record_count
            FROM sentiment_summary
            WHERE major = ?
        """
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, (major,))
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "weighted_pos_total": row["weighted_pos_total"],
                "weighted_neg_total": row["weighted_neg_total"],
                "total_likes": row["total_likes"],
                "record_count": row["record_count"]
            }