# backend/services/process/cleaning/public/base_database_manager.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
from loguru import logger


class BaseDatabaseManager:
    """
    数据库管理基类。
    提供基础的 SQL 执行、查询和流式读取功能。
    支持上下文管理器 (with 语句) 以自动关闭连接。
    """

    def __init__(self, db_path: str):
        """
        初始化数据库连接。
        :param db_path: 数据库文件路径 (str)
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

        # 确保数据库目录存在
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self._connect()

    def _connect(self):
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            # 设置行工厂，以便可以通过列名访问数据 (row['column_name'])
            self.conn.row_factory = sqlite3.Row
            logger.debug(f"数据库连接已建立：{self.db_path}")

    def _disconnect(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("数据库连接已关闭")

    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行 SELECT 查询，返回字典列表。
        """
        if not self.conn:
            self._connect()

        cursor = None
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SQL Query 失败：{e} | SQL: {sql} | Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行 INSERT/UPDATE/DELETE 操作，返回受影响的行数。
        """
        if not self.conn:
            self._connect()

        cursor = None
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"SQL Update 失败：{e} | SQL: {sql} | Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_many_update(self, sql: str, params_list: List[tuple]) -> int:
        """
        执行批量 INSERT/UPDATE/DELETE 操作，返回受影响的总行数。
        :param sql: SQL 语句（使用 ? 占位符）
        :param params_list: 参数列表，每个元素是一个元组，对应一条记录的参数
        :return: 受影响的行数总和
        """
        if not self.conn:
            self._connect()

        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.executemany(sql, params_list)
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"SQL Batch Update 失败：{e} | SQL: {sql} | Params count: {len(params_list)}")
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_stream_query(self, sql: str, params: tuple = None) -> Generator[Dict[str, Any], None, None]:
        """
        流式执行查询，逐行 yield 结果（节省内存）。
        """
        if not self.conn:
            self._connect()

        cursor = None
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # 迭代游标
            for row in cursor:
                yield dict(row)
        except Exception as e:
            logger.error(f"SQL Stream 失败：{e} | SQL: {sql} | Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()

    def close(self):
        """显式关闭数据库连接"""
        self._disconnect()

    # --- 上下文管理器支持 (支持 with 语句) ---
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        # 返回 False 让异常继续抛出，返回 True 则吞掉异常
        return False