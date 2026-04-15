# 适合云算力的全量内存处理版本
import sqlite3
from typing import Optional, Tuple, List
from pathlib import Path
from loguru import logger
from datetime import datetime

from backend.services.process.cleaning.public.base_database_manager import BaseDatabaseManager


class JobDataReader(BaseDatabaseManager):
    """
    涉及数据库：job_data
    用于清洗数据时和数据库的交互（针对多线程/内存预加载优化版）
    """

    TABLE_NAME = "parsed_jobs"

    def __init__(self, db_path: Path):
        super().__init__(str(db_path))

        logger.debug(f"初始化全局职位读取器：{db_path}")

        # --- 性能优化关键代码 ---
        try:
            self.conn.execute("PRAGMA synchronous = OFF;")
            self.conn.execute("PRAGMA journal_mode = MEMORY;")
            logger.debug("SQLite 性能优化已应用 (synchronous=OFF)")
        except Exception as e:
            logger.warning(f"SQLite 优化设置失败: {e}")

    # --- 内存预加载支持 ---

    def get_all_pending_data(self) -> List[Tuple[str, str, str]]:
        sql = f"""
        SELECT job_id, major_name, job_description 
        FROM "{self.TABLE_NAME}" 
        WHERE processed_at IS NULL
        """
        try:
            rows = self.execute_query(sql)
            if not rows:
                return []
            return [(row['job_id'], row['major_name'], row['job_description']) for row in rows]
        except Exception as e:
            logger.error(f"全量读取数据失败: {e}")
            return []

    def batch_mark_processed(self, id_pairs: List[Tuple[str, str]]) -> int:
        """
        批量标记为已处理（基于复合主键）。
        :param id_pairs: [(job_id, major_name), ...]
        :return: 受影响的行数
        """
        if not id_pairs:
            return 0
        sql = f"""
        UPDATE "{self.TABLE_NAME}" 
        SET processed_at = ? 
        WHERE job_id = ? AND major_name = ?
        """
        params = []
        now = datetime.now().isoformat()
        for job_id, major_name in id_pairs:
            params.append((now, job_id, major_name))
        try:
            return self.execute_many_update(sql, params)  # 需实现 execute_many_update
        except Exception as e:
            logger.error(f"批量更新状态失败: {e}")
            return 0

    # --- 新增方法：重置所有记录的 processed_at 为 NULL ---
    def reset_all_processed_at(self) -> int:
        """
        将表中所有记录的 processed_at 字段重置为 NULL。
        警告：此操作会清除所有处理标记，通常用于重新处理全部数据。
        :return: 受影响的行数
        """
        sql = f'UPDATE "{self.TABLE_NAME}" SET processed_at = NULL'
        try:
            rows_affected = self.execute_update(sql)
            logger.warning(f"已重置所有记录的 processed_at 字段，共 {rows_affected} 行受影响")
            return rows_affected
        except Exception as e:
            logger.error(f"重置 processed_at 失败: {e}")
            return 0

    # --- 辅助方法 ---

    def get_all_pending_ids(self) -> List[str]:
        sql = f"""
        SELECT job_id 
        FROM "{self.TABLE_NAME}" 
        WHERE processed_at IS NULL
        """
        try:
            cursor = self.conn.execute(sql)
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取待处理 ID 列表失败: {e}")
            return []

    def get_stats(self) -> dict:
        total_sql = f"SELECT COUNT(*) as c FROM \"{self.TABLE_NAME}\""
        pending_sql = f"SELECT COUNT(*) as c FROM \"{self.TABLE_NAME}\" WHERE processed_at IS NULL"
        total_res = self.execute_query(total_sql)
        pending_res = self.execute_query(pending_sql)
        total = total_res[0]['c'] if total_res else 0
        pending = pending_res[0]['c'] if pending_res else 0
        return {
            "total": total,
            "pending": pending,
            "processed": total - pending
        }