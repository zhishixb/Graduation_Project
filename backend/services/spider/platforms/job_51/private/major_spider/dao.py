# --- 专业解析后数据存储管理器 ---
import sqlite3
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any
from datetime import datetime

from backend.services.spider.platforms.job_51.public.base_database_manager import BaseDatabaseManager

import sqlite3
from contextlib import contextmanager


class JobDatabaseManager(BaseDatabaseManager):  # 假设 BaseDatabaseManager
    """
    涉及数据库：job_data
    用于爬虫操作中数据存储
    """
    TABLE_NAME = "parsed_jobs"
    EXTRA_COLUMNS = {"processed_at": "TEXT DEFAULT NULL"}

    def __init__(self, db_path: Path, major_name: str):
        self.db_path = str(db_path)  # 只存路径！
        self.major_name = major_name
        self._initialize_schema()  # 注意：这个方法也要改！

    @contextmanager
    def _get_connection(self):
        """
        线程安全的连接上下文管理器
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 保持你原有的 dict-like 行支持
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            conn.close()

    def _initialize_schema(self):
        """
        创建/确认表结构
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. 创建表
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{self.TABLE_NAME}" (
                job_id TEXT NOT NULL,
                major_name TEXT NOT NULL,
                job_name TEXT,
                industry_type TEXT,
                job_description TEXT,
                processed_at TEXT DEFAULT NULL,
                PRIMARY KEY (job_id, major_name)
            );
            """
            cursor.execute(create_table_sql)

            # 2. 创建索引
            index_major = f'CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_major ON "{self.TABLE_NAME}" (major_name);'
            index_job_id = f'CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_job_id ON "{self.TABLE_NAME}" (job_id);'
            index_processed = f'CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_processed ON "{self.TABLE_NAME}" (major_name, processed_at);'

            cursor.execute(index_major)
            cursor.execute(index_job_id)
            cursor.execute(index_processed)

            # 3. Schema migration
            cursor.execute(f'PRAGMA table_info("{self.TABLE_NAME}");')
            existing_columns = {row[1] for row in cursor.fetchall()}
            for col_name, col_def in self.EXTRA_COLUMNS.items():
                if col_name not in existing_columns:
                    logger.info(f"检测到表 '{self.TABLE_NAME}' 缺少列 '{col_name}'，正在执行迁移...")
                    alter_sql = f'ALTER TABLE "{self.TABLE_NAME}" ADD COLUMN "{col_name}" {col_def};'
                    try:
                        cursor.execute(alter_sql)
                        logger.success(f"✅ 成功添加列: {col_name}")
                    except sqlite3.Error as e:
                        logger.error(f"❌ 添加列 {col_name} 失败: {e}")

        logger.info(f"解析后数据表 '{self.TABLE_NAME}' 结构检查完成。")

    def insert_parsed_data(self, parsed_data_list: List[Dict[str, Any]]) -> bool:
        """
        将爬取的数据列表存储入数据库

        Args:
            parsed_data_list:

        Returns:
            是否插入成功
        """
        if not parsed_data_list:
            logger.warning(f"没有解析后的数据需要插入（专业: {self.major_name}）。")
            return True

        insert_sql = f"""
        INSERT OR IGNORE INTO "{self.TABLE_NAME}" 
            (job_id, major_name, job_name, industry_type, job_description)
        VALUES (?, ?, ?, ?, ?);
        """

        records_to_insert = []
        skip_count = 0
        for item in parsed_data_list:
            job_id = item.get('jobId')
            if not job_id:
                logger.warning("警告：发现缺失 job_id 的记录，将跳过。")
                skip_count += 1
                continue
            records_to_insert.append((
                job_id,
                self.major_name,
                item.get('jobName'),
                item.get('industryType2Str'),
                item.get('jobDescribe')
            ))

        if not records_to_insert:
            return True

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(insert_sql, records_to_insert)
                rows_affected = cursor.rowcount
                logger.info(
                    f"[{self.major_name}] 尝试插入 {len(records_to_insert)} 条记录，"
                    f"实际新增 {rows_affected} 条，跳过 {skip_count} 条无效数据。"
                )
            return True
        except sqlite3.Error as e:
            logger.error(f"批量插入数据失败（专业: {self.major_name}）: {e}")
            return False