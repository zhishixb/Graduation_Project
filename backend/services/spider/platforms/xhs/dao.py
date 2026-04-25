import sqlite3
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class CommentDataManager:
    """将解析后的评论数据存储到 SQLite 数据库"""

    TABLE_NAME = "comments"
    SCHEMA = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major TEXT NOT NULL,
            note_id TEXT NOT NULL,
            content TEXT,
            like_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(major, note_id, content) ON CONFLICT IGNORE
        )
    """

    def __init__(self, db_path: Union[str, Path], auto_init: bool = True):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        if auto_init:
            self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        with conn:
            conn.execute(self.SCHEMA)

    def save_comments(self, comments: List[Dict[str, Any]], major: str) -> int:
        if not comments:
            return 0
        conn = self._get_connection()
        rows = []
        for item in comments:
            try:
                like_count = int(item.get('like_count', 0))
            except (ValueError, TypeError):
                like_count = 0
            rows.append((major, item['note_id'], item['content'], like_count))
        with conn:
            cursor = conn.executemany(
                f"INSERT OR IGNORE INTO {self.TABLE_NAME} (major, note_id, content, like_count) VALUES (?, ?, ?, ?)",
                rows
            )
            return cursor.rowcount

    def get_comments_by_note(self, note_id: str, major: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        if major:
            cursor = conn.execute(
                f"SELECT major, note_id, content, like_count FROM {self.TABLE_NAME} WHERE note_id = ? AND major = ?",
                (note_id, major)
            )
        else:
            cursor = conn.execute(
                f"SELECT major, note_id, content, like_count FROM {self.TABLE_NAME} WHERE note_id = ?",
                (note_id,)
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def note_exists(self, note_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.execute(
            f"SELECT 1 FROM {self.TABLE_NAME} WHERE note_id = ? LIMIT 1",
            (note_id,)
        )
        return cursor.fetchone() is not None

    def get_statistics(self, major: Optional[str] = None) -> Dict[str, int]:
        conn = self._get_connection()
        if major:
            cursor = conn.execute(f"""
                SELECT 
                    COUNT(*) AS total_comments,
                    COUNT(DISTINCT note_id) AS total_notes
                FROM {self.TABLE_NAME}
                WHERE major = ?
            """, (major,))
        else:
            cursor = conn.execute(f"""
                SELECT 
                    COUNT(*) AS total_comments,
                    COUNT(DISTINCT note_id) AS total_notes
                FROM {self.TABLE_NAME}
            """)
        row = cursor.fetchone()
        return {
            'total_comments': row['total_comments'],
            'total_notes': row['total_notes']
        }

    # ---------- 新增方法 ----------
    def count_by_major(self, major: str) -> int:
        """
        查询指定专业下的评论总条数

        :param major: 专业名称
        :return: 该专业下的评论数量（整数），若表为空或无该专业则返回 0
        """
        conn = self._get_connection()
        cursor = conn.execute(
            f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE major = ?",
            (major,)
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()