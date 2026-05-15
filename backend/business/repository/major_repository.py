import sqlite3
from pathlib import Path
from typing import List, Dict

class MajorRepository:
    def __init__(self, db_path: Path):
        self._db_path = db_path

    def get_top_majors_by_heat(self, limit: int = 30) -> List[Dict[str, object]]:
        """按 heat_value 降序返回前 N 条专业的 name 与热度值"""
        query = """
            SELECT name, heat_value
            FROM majors
            ORDER BY heat_value DESC
            LIMIT ?
        """
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, (limit,))
            return [{"name": row["name"], "heat_value": row["heat_value"]} for row in cur]