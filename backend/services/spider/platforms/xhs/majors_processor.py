import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Union, Dict, Any


class MajorsProcessor:
    """
    管理 majors 表处理状态的工具类

    is_processed 状态约定：
        - 0 : 处理失败或待重试
        - 1 : 已成功处理
        - NULL : 从未处理过（初始状态）
    """

    def __init__(self, db_path: Union[str, Path]):
        """
        :param db_path: SQLite 数据库文件路径（支持字符串或 Path 对象）
        """
        self.db_path = str(Path(db_path).resolve())
        self._ensure_processed_column()

    def _get_connection(self):
        """获取数据库连接（自动开启外键约束等）"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_processed_column(self):
        """确保表中存在 is_processed 字段（如不存在则自动添加）"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(majors)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'is_processed' not in columns:
                cursor.execute("ALTER TABLE majors ADD COLUMN is_processed INTEGER DEFAULT NULL")
                conn.commit()
                print("✅ 已自动添加字段 'is_processed'")
        finally:
            conn.close()

    # ---------- 状态标记方法 ----------
    def _set_processed_status(self, name: str, status: int) -> bool:
        """内部通用状态更新"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE majors SET is_processed = ? WHERE name = ?",
                (status, name)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"状态更新失败: {e}")
            return False
        finally:
            conn.close()

    def mark_processed_by_name(self, name: str, status_value: int = 0) -> bool:
        return self._set_processed_status(name, status_value)

    # ---------- 查询方法 ----------
    def get_first_unprocessed(self) -> Optional[Dict[str, Any]]:
        """
        获取第一条未成功处理的记录（is_processed != 1）
        :return: 包含 name 和 is_processed 的字典，若无则返回 None
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, is_processed FROM majors "
                "WHERE is_processed IS NULL OR is_processed != 1 "
                "ORDER BY id LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return {"name": row["name"], "is_processed": row["is_processed"]}
            return None
        finally:
            conn.close()

    def get_first_unprocessed_name(self) -> Optional[str]:
        """
        获取第一条未成功处理的专业名称（仅 name）
        """
        result = self.get_first_unprocessed()
        return result["name"] if result else None

    def get_all_status_as_json(self, ensure_ascii: bool = False) -> str:
        """
        将表中所有记录的 name 和 is_processed 字段以 JSON 字符串返回

        :param ensure_ascii: 是否转义非 ASCII 字符，默认 False 保留中文
        :return: JSON 字符串，格式为 [{"name": "计算机", "is_processed": 1}, ...]
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, is_processed FROM majors ORDER BY id")
            rows = cursor.fetchall()
            result = [{"name": row["name"], "is_processed": row["is_processed"]} for row in rows]
            return json.dumps(result, ensure_ascii=ensure_ascii)
        finally:
            conn.close()

    # ---------- 重置方法 ----------
    def reset_all_processed(self):
        """重置所有记录的 is_processed 为 NULL（用于测试或重新处理）"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE majors SET is_processed = NULL")
            conn.commit()
            print(f"已重置 {cursor.rowcount} 条记录的处理状态")
        finally:
            conn.close()