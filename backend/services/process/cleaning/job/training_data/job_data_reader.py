# backend/services/process/cleaning/job_data_reader.py
import re
from typing import Optional, Tuple
from pathlib import Path  # 1. 导入 Path
from loguru import logger
from datetime import datetime

from backend.services.process.cleaning.public.base_database_manager import BaseDatabaseManager


class JobDataReader(BaseDatabaseManager):
    """
    涉及数据库：job_data（存储按照专业就业方向爬取的微调前体数据）
    用于清洗数据时和数据库的交互
    """

    TABLE_NAME = "parsed_jobs"

    def __init__(self, db_path: Path):  # 2. 修改类型提示为 Path
        super().__init__(str(db_path))

        logger.debug(f"初始化全局职位读取器：{db_path}")  # loguru 可以直接打印 Path 对象

    def get_next_unprocessed(self) -> Optional[Tuple[str, str, str]]:
        """
        获取全库中任意一条未处理的数据。
        :return: (job_id, description) 或 None
        """
        sql = f"""
        SELECT job_id, major_name, job_description 
        FROM "{self.TABLE_NAME}" 
        WHERE processed_at IS NULL 
        LIMIT 1;
        """
        rows = self.execute_query(sql)

        if not rows:
            return None

        row = rows[0]
        job_id = row.get('job_id')
        major_name = row.get('major_name')
        desc = row.get('job_description')

        if not job_id or not desc:
            if job_id:
                self.mark_processed(job_id)
            return None

        return job_id, major_name, desc.strip()

    def get_pending_count(self) -> int:
        """
        返回全库未处理记录数
        """
        sql = f"SELECT COUNT(*) as c FROM \"{self.TABLE_NAME}\" WHERE processed_at IS NULL"
        res = self.execute_query(sql)
        return res[0]['c'] if res else 0

    def mark_processed(self, job_id: str) -> bool:
        """
        按照job_id标记为已处理
        """
        sql = f"""
        UPDATE "{self.TABLE_NAME}" 
        SET processed_at = ? 
        WHERE job_id = ?;
        """
        ts = datetime.now().isoformat()
        affected = self.execute_update(sql, (ts, job_id))
        return affected > 0

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