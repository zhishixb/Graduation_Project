import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple, Iterator, Generator
from contextlib import contextmanager

class BaseDatabaseManager:
    """
    数据库管理器基类 (增强版)
    支持：
    1. 统一连接管理
    2. 批量查询 (fetchall)
    3. 流式查询 (iterator/cursor)
    4. 上下文管理器 (with statement)
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

    @staticmethod
    def _ensure_db_dir(db_path: str):
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    @classmethod
    def _get_connection(cls, db_path: str) -> sqlite3.Connection:
        cls._ensure_db_dir(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 关键：支持 dict 风格访问
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _connect(self):
        if not self.connection:
            self.connection = self._get_connection(self.db_path)

    def _disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    # --- 新增：上下文管理器支持 ---
    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._disconnect()
        return False  # 不吞掉异常

    # --- 新增：获取配置好的 Cursor (用于高级自定义操作) ---
    def get_cursor(self) -> sqlite3.Cursor:
        self._connect()
        if not self.connection:
            raise sqlite3.Error("Connection failed")
        return self.connection.cursor()

    # --- 新增：流式执行方法 (核心改动) ---
    def execute_stream_query(self, query: str, params: tuple = ()) -> Iterator[sqlite3.Row]:
        """
        执行 SELECT 查询并返回一个迭代器。
        数据是逐行从磁盘读取的，不会一次性加载到内存。
        调用者负责关闭 cursor 和 connection (通常配合 with 语句使用)。
        """
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params)
            # cursor 本身就是一个迭代器
            yield from cursor
        finally:
            # 注意：这里不关闭 connection，因为可能还要复用
            # 但必须关闭当前 cursor
            cursor.close()

    # --- 原有方法保留 (用于小数据量查询) ---
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """执行查询并返回所有结果列表 (适合小数据量)"""
        with self.get_cursor() as cursor: # 使用 cursor 的上下文管理器
            cursor.execute(query, params)
            return cursor.fetchall()
        # connection 由外层或显式调用管理

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """执行更新操作"""
        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"执行更新时出错: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
            # 注意：这里可以选择是否断开连接，视业务需求而定
            # self._disconnect()