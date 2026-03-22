import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from loguru import logger


class BaseDatabaseManager:
    """
    数据库管理基类。
    提供基础的 SQL 执行、查询和流式读取功能。
    修复了 sqlite3.Cursor 不支持上下文管理器的问题。
    """

    def __init__(self, db_path: str):
        """
        初始化数据库连接。
        :param db_path: 数据库文件路径 (str)
        """
        self.db_path = db_path

        # 确保数据库目录存在
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # 建立连接
        self.conn = sqlite3.connect(db_path)
        # 设置行工厂，以便可以通过列名访问数据 (row['column_name'])
        self.conn.row_factory = sqlite3.Row

        logger.debug(f"数据库连接已建立：{db_path}")

    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行 SELECT 查询，返回字典列表。
        """
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
            self.conn.rollback()
            logger.error(f"SQL Update 失败：{e} | SQL: {sql} | Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_stream_query(self, sql: str, params: tuple = None) -> Generator[Dict[str, Any], None, None]:
        """
        流式执行查询，逐行 yield 结果（节省内存）。
        """
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
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.debug("数据库连接已关闭")