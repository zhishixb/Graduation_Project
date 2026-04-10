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

        # 1. 关闭同步模式 (大幅提升 UPDATE 速度)
        # 默认是 FULL，每次写入都要等待磁盘确认。设为 OFF 后速度提升数倍。
        # 风险：仅在电脑突然断电时可能丢失最后几秒数据，程序崩溃不影响。
        try:
            self.conn.execute("PRAGMA synchronous = OFF;")
            self.conn.execute("PRAGMA journal_mode = MEMORY;")
            logger.debug("SQLite 性能优化已应用 (synchronous=OFF)")
        except Exception as e:
            logger.warning(f"SQLite 优化设置失败: {e}")

    # --- 内存预加载支持 ---

    def get_all_pending_data(self) -> List[Tuple[str, str, str]]:
        """
        【核心方法】一次性获取所有待处理数据到内存。
        :return: List[(job_id, major_name, job_description), ...]
        """
        sql = f"""
        SELECT job_id, major_name, job_description 
        FROM "{self.TABLE_NAME}" 
        WHERE processed_at IS NULL
        """
        try:
            rows = self.execute_query(sql)
            if not rows:
                return []

            # 转换为元组列表，方便多线程解包
            return [
                (row['job_id'], row['major_name'], row['job_description'])
                for row in rows
            ]
        except Exception as e:
            logger.error(f"全量读取数据失败: {e}")
            return []

    def batch_mark_processed(self, job_ids: List[str]) -> int:
        """
        【核心方法】批量标记为已处理。
        使用 SQL IN 语句一次性更新，避免多线程频繁锁库。
        :param job_ids: 待更新的 ID 列表
        :return: 受影响的行数
        """
        if not job_ids:
            return 0

        # 构造 (?, ?, ?, ...) 占位符
        placeholders = ','.join('?' * len(job_ids))

        sql = f"""
        UPDATE "{self.TABLE_NAME}" 
        SET processed_at = ? 
        WHERE job_id IN ({placeholders});
        """

        # 参数：(当前时间, id1, id2, ...)
        params = [datetime.now().isoformat()] + job_ids

        try:
            return self.execute_update(sql, params)
        except Exception as e:
            logger.error(f"批量更新状态失败: {e}")
            return 0

    # --- 🛠️ 辅助方法 ---

    def get_all_pending_ids(self) -> List[str]:
        """
        获取所有待处理任务的 ID 列表。
        用于 tqdm 进度条计算总数（如果不使用内存预加载模式）。
        """
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
        """
        获取全库统计信息
        """
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