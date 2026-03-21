# --- 专业解析后数据存储管理器 ---
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from backend.services.spider.platforms.job_51.public.base_database_manager import BaseDatabaseManager


class JobDatabaseManager(BaseDatabaseManager):
    """
    专业解析后数据存储管理器，为指定专业创建和管理存储解析后数据的SQLite表。
    表名即为专业名。
    """

    def __init__(self, db_path: Path, major_name: str): # 修改参数类型为 Path
        # 将 Path 对象转换为字符串，传递给父类构造函数
        super().__init__(str(db_path))

        self.table_name = major_name
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        """
        创建用于存储解析后数据的表。
        """
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS "{self.table_name}" (
            job_id TEXT NOT NULL PRIMARY KEY,       -- 业务主键，职位的唯一ID
            job_name TEXT,                          -- 职位名称
            industry_type TEXT,                     -- 公司行业
            job_description TEXT                    -- 职位描述
        );
        """
        # 为常用查询字段创建索引
        index_job_id = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_job_id ON \"{self.table_name}\" (job_id);"

        self.execute_update(create_table_sql)
        self.execute_update(index_job_id)
        print(f"解析后数据表 '{self.table_name}' 已准备好。")

    def insert_parsed_data(self, parsed_data_list: Tuple[bool, Optional[List[Dict[str, Any]]], str]) -> bool:
        """
        将解析后的数据列表插入到对应专业的表中。

        :param parsed_data_list: JobDataParser.parse_listings() 返回的职位列表
        :return: 操作成功返回 True，否则返回 False
        """
        if not parsed_data_list:
            print(f"没有解析后的数据需要插入到表 '{self.table_name}'。")
            return True

        insert_sql = f"""
        INSERT OR IGNORE INTO "{self.table_name}" (job_id, job_name, industry_type, job_description)
        VALUES (?, ?, ?, ?);
        """

        records_to_insert = []
        for item in parsed_data_list:
            job_id = item.get('jobId')
            if not job_id:
                print("警告：发现缺失 job_id 的记录，将跳过。")
                continue

            record = (
                job_id,
                item.get('jobName'),
                item.get('industryType2Str'),
                item.get('jobDescribe')
            )
            records_to_insert.append(record)

        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.executemany(insert_sql, records_to_insert)
            self.connection.commit()

            rows_affected = cursor.rowcount
            print(f"尝试插入 {len(records_to_insert)} 条记录，实际成功插入或更新了 {rows_affected} 条。")
            return True
        except sqlite3.Error as e:
            print(f"批量插入数据到表 '{self.table_name}' 时出错: {e}")
            self.connection.rollback()
            return False
        finally:
            self._disconnect()