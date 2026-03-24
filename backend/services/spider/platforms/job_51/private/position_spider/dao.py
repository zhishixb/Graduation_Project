# --- 专业解析后数据存储管理器 ---
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from backend.services.spider.platforms.job_51.public.base_database_manager import BaseDatabaseManager


class JobDatabaseManager(BaseDatabaseManager):
    """
    专业解析后数据存储管理器。
    所有数据存储在同一张表 'job_list' 中，通过 major 和 function 字段区分。
    """

    def __init__(self, db_path: Path, default_function: str):
        """
        初始化数据库管理器。

        :param db_path: 数据库文件路径
        :param major_name: 默认的专业名称，将作为插入数据时 'major' 字段的默认值
        :param default_function: 默认的职能分类，将作为插入数据时 'function' 字段的默认值
        """
        super().__init__(str(db_path))

        self.table_name = "job_list"
        self.default_function = default_function

        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        """
        创建用于存储解析后数据的通用表 'job_list'。
        """
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS "{self.table_name}" (
            job_id TEXT NOT NULL PRIMARY KEY,       -- 业务主键，职位的唯一ID
            job_name TEXT,                          -- 职位名称
            industry_type TEXT,                     -- 公司行业
            job_description TEXT,                   -- 职位描述
            function TEXT,                          -- 职能分类 (新增)
            salary TEXT,                            -- 薪资范围 (新增)
            major TEXT,                             -- 关联专业 (新增)
            provinceCode TEXT                       -- 省份代码 (新增)
        );
        """
        # 为常用查询字段创建索引，提高检索效率
        # 联合索引 (major, function) 对于按专业和职能筛选非常有效
        index_main = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_major_func ON \"{self.table_name}\" (major, function);"
        index_job_id = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_job_id ON \"{self.table_name}\" (job_id);"
        index_province = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_province ON \"{self.table_name}\" (provinceCode);"

        self.execute_update(create_table_sql)
        self.execute_update(index_main)
        self.execute_update(index_job_id)
        self.execute_update(index_province)

        print(
            f"通用职位数据表 '{self.table_name}' 已准备好, 默认职能: {self.default_function})。")

    def insert_parsed_data(self, parsed_data_list: List[Dict[str, Any]],
                           override_function: Optional[str] = None) -> bool:
        """
        将解析后的数据列表插入到 'job_list' 表中。

        :param parsed_data_list: JobDataParser.parse_listings() 返回的职位列表
        :param override_function: 可选，如果提供，则覆盖实例默认的 function 值。
                                  如果列表中的项自己有 'function' 字段，优先使用项里的，否则使用此参数或默认值。
        :return: 操作成功返回 True，否则返回 False
        """
        if not parsed_data_list:
            print(f"没有解析后的数据需要插入到表 '{self.table_name}'。")
            return True

        # 确定本次插入使用的 function 值
        target_function = override_function if override_function else self.default_function

        insert_sql = f"""
        INSERT OR IGNORE INTO "{self.table_name}" 
        (job_id, job_name, industry_type, job_description, function, salary, major, provinceCode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        records_to_insert = []
        for item in parsed_data_list:
            job_id = item.get('jobId')
            if not job_id:
                print("警告：发现缺失 job_id 的记录，将跳过。")
                continue

            # 优先级逻辑：
            # 1. 尝试从 item 中获取具体字段
            # 2. 如果没有，则使用类初始化的默认值

            # function: 优先取 item 里的，其次取传入的 override，最后取实例默认值
            item_function = item.get('function') or item.get('category')  # 兼容可能的不同 key
            final_function = item_function if item_function else target_function

            record = (
                job_id,
                item.get('jobName'),
                item.get('industryType2Str'),
                item.get('jobDescribe'),
                final_function,  # 新字段：function
                item.get('provideSalaryString'),  # 新字段：salary (可能为 None)
                item.get('major1Str'),
                item.get('jobAreaCode')  # 新字段：provinceCode (可能为 None)
            )
            records_to_insert.append(record)

        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.executemany(insert_sql, records_to_insert)
            self.connection.commit()

            rows_affected = cursor.rowcount
            print(f"尝试插入 {len(records_to_insert)} 条记录到 '{self.table_name}'，实际成功入库 {rows_affected} 条。")
            return True
        except sqlite3.Error as e:
            print(f"批量插入数据到表 '{self.table_name}' 时出错: {e}")
            self.connection.rollback()
            return False
        finally:
            self._disconnect()

    def get_random_job_by_function(self, function: str) -> Optional[Dict[str, Any]]:
        """
        根据指定的职能 (function) 随机返回一条职位数据。

        :param function: 职能分类字符串 (例如: 'Java开发', '产品经理')
        :return: 如果找到数据，返回包含字段信息的字典；如果没有找到或出错，返回 None
        """
        if not function:
            print("错误：function 参数不能为空。")
            return None

        query_sql = f"""
        SELECT job_id, job_name, industry_type, job_description, function, salary, major, provinceCode
        FROM "{self.table_name}"
        WHERE function = ?
        ORDER BY RANDOM()
        LIMIT 1;
        """

        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query_sql, (function,))
            row = cursor.fetchone()

            if row:
                # 将元组转换为字典，方便调用者使用
                columns = [desc[0] for desc in cursor.description]
                result_dict = dict(zip(columns, row))

                return result_dict
            else:
                print(f"未找到职能为 '{function}' 的任何职位数据。")
                return None

        except sqlite3.Error as e:
            print(f"随机查询职位时出错: {e}")
            return None
        finally:
            self._disconnect()