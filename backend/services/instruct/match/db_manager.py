import sqlite3
from pathlib import Path
from typing import List, Tuple

class DatabaseManager:
    """
    SQLite 数据库操作类，用于存储岗位-专业相似度矩阵。
    仅包含建表和批量插入功能。
    """
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._conn = None

    def _connect(self) -> sqlite3.Connection:
        """获取数据库连接（自动创建目录）"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def create_table(self):
        """创建相似度表，以 (function_name, major_name) 为主键"""
        conn = self._connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_major_similarity (
                function_name TEXT NOT NULL,
                major_name TEXT NOT NULL,
                similarity REAL NOT NULL,
                PRIMARY KEY (function_name, major_name)
            )
        """)
        conn.commit()

    def insert_batch(self, data: List[Tuple[str, str, float]]):
        """
        批量插入或替换相似度数据。
        :param data: 列表，每个元素为 (function_name, major_name, similarity)
        """
        if not data:
            return
        conn = self._connect()
        conn.execute("BEGIN TRANSACTION")
        conn.executemany(
            "INSERT OR REPLACE INTO job_major_similarity VALUES (?, ?, ?)",
            data
        )
        conn.commit()

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()