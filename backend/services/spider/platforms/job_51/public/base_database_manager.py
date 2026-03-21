import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple


# --- 基础数据库管理类 ---
class BaseDatabaseManager:
    """
    数据库管理器基类，提供通用的连接、目录管理和辅助方法。
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    @staticmethod
    def _ensure_db_dir(db_path: str):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    @classmethod
    def _get_connection(cls, db_path: str) -> sqlite3.Connection:
        """获取数据库连接，并设置基础配置"""
        cls._ensure_db_dir(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 设置row_factory，方便通过列名访问
        conn.execute("PRAGMA foreign_keys = ON")  # 如需外键约束
        return conn

    def _connect(self):
        """打开数据库连接"""
        if not self.connection:
            self.connection = self._get_connection(self.db_path)

    def _disconnect(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        执行一个SELECT查询并返回结果。

        :param query: SQL 查询语句
        :param params: 查询参数
        :return: 查询结果列表
        """
        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"执行查询时出错: {e}")
            return []
        finally:
            self._disconnect()

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """
        执行一个INSERT, UPDATE, 或 DELETE 语句。

        :param query: SQL 更新语句
        :param params: 语句参数
        :return: 操作成功返回 True，否则返回 False
        """
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
            self._disconnect()