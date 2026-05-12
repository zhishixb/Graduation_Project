import sqlite3
from pathlib import Path
from typing import List, Tuple

class JobLocationRepository:
    def __init__(self, db_path: Path):
        self._db_path = db_path

    def get_province_counts(self, job_names: List[str]) -> List[Tuple[str, int]]:
        """返回 [(原始provinceCode, count), ...]"""
        if not job_names:
            return []

        placeholders = ",".join(["?"] * len(job_names))
        query = f"""
            SELECT provinceCode, COUNT(*) AS cnt
            FROM position_jobs
            WHERE function IN ({placeholders})
            GROUP BY provinceCode
        """
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, job_names)
            rows = cur.fetchall()
        return [(row["provinceCode"], row["cnt"]) for row in rows]