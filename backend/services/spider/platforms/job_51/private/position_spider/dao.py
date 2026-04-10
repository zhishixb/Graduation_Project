# --- 专业解析后数据存储管理器 ---
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from loguru import logger

from backend.services.spider.platforms.job_51.public.base_database_manager import BaseDatabaseManager


class JobDatabaseManager(BaseDatabaseManager):
    """
    专业解析后数据存储管理器。
    所有数据存储在同一张表 'job_list' 中，通过 major 和 function 字段区分。
    """

    # 定义额外字段及其SQL定义（用于自动迁移）
    EXTRA_COLUMNS = {
        "processed_at": "TEXT DEFAULT NULL",  # 处理时间戳字段
        # 未来可以继续添加其他字段，例如：
        # "updated_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        # "data_source": "TEXT DEFAULT '51job'",
    }

    def __init__(self, db_path: Path, default_function: str):
        """
        初始化数据库管理器。

        :param db_path: 数据库文件路径
        :param major_name: 默认的专业名称，将作为插入数据时 'major' 字段的默认值
        :param default_function: 默认的职能分类，将作为插入数据时 'function' 字段的默认值
        """
        super().__init__(str(db_path))

        self.table_name = "position_jobs"
        self.default_function = default_function

        self._create_table_if_not_exists()
        self._migrate_schema()  # 添加 schema 迁移

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
            provinceCode TEXT,                      -- 省份代码 (新增)
            processed_at TEXT DEFAULT NULL          -- 处理时间戳字段
        );
        """
        # 为常用查询字段创建索引，提高检索效率
        # 联合索引 (major, function) 对于按专业和职能筛选非常有效
        index_main = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_major_func ON \"{self.table_name}\" (major, function);"
        index_job_id = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_job_id ON \"{self.table_name}\" (job_id);"
        index_province = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_province ON \"{self.table_name}\" (provinceCode);"
        index_processed = f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_processed ON \"{self.table_name}\" (processed_at);"

        self.execute_update(create_table_sql)
        self.execute_update(index_main)
        self.execute_update(index_job_id)
        self.execute_update(index_province)
        self.execute_update(index_processed)

        logger.info(f"通用职位数据表 '{self.table_name}' 已准备好, 默认职能: {self.default_function})。")

    def _migrate_schema(self):
        """
        自动迁移数据库表结构，添加缺失的字段。
        用于处理已存在的表需要添加新字段的情况。
        """
        try:
            # 获取当前表的列信息
            pragma_sql = f'PRAGMA table_info("{self.table_name}");'
            self._connect()
            cursor = self.connection.cursor()
            cursor.execute(pragma_sql)
            existing_columns = {row[1] for row in cursor.fetchall()}
            self._disconnect()

            # 检查并添加缺失的字段
            for col_name, col_def in self.EXTRA_COLUMNS.items():
                if col_name not in existing_columns:
                    logger.info(f"检测到表 '{self.table_name}' 缺少列 '{col_name}'，正在执行迁移...")
                    alter_sql = f'ALTER TABLE "{self.table_name}" ADD COLUMN "{col_name}" {col_def};'
                    try:
                        self.execute_update(alter_sql)
                        logger.success(f"✅ 成功添加列: {col_name}")

                        # 为新添加的字段创建索引（如果需要）
                        if col_name == "processed_at":
                            index_sql = f'CREATE INDEX IF NOT EXISTS idx_{self.table_name}_{col_name} ON "{self.table_name}" ({col_name});'
                            self.execute_update(index_sql)
                    except sqlite3.Error as e:
                        logger.error(f"❌ 添加列 {col_name} 失败: {e}")

        except sqlite3.Error as e:
            logger.error(f"Schema 迁移检查失败: {e}")

    def insert_parsed_data(self, parsed_data_list: List[Dict[str, Any]],
                           override_function: Optional[str] = None,
                           update_processed_at: bool = True) -> Tuple[bool, int]:
        """
        将解析后的数据列表插入到 'job_list' 表中。

        :param parsed_data_list: JobDataParser.parse_listings() 返回的职位列表
        :param override_function: 可选，如果提供，则覆盖实例默认的 function 值。
                                  如果列表中的项自己有 'function' 字段，优先使用项里的，否则使用此参数或默认值。
        :param update_processed_at: 是否在插入时设置 processed_at 为当前时间戳，默认 True
        :return: 操作成功返回 True，否则返回 False
        """
        if not parsed_data_list:
            logger.warning(f"没有解析后的数据需要插入到表 '{self.table_name}'。")
            return True, 0

        # 确定本次插入使用的 function 值
        target_function = override_function if override_function else self.default_function

        # 获取当前时间戳（如果需要）
        current_timestamp = datetime.now().isoformat() if update_processed_at else None

        insert_sql = f"""
        INSERT OR IGNORE INTO "{self.table_name}" 
        (job_id, job_name, industry_type, job_description, function, salary, major, provinceCode, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        records_to_insert = []
        for item in parsed_data_list:
            job_id = item.get('jobId')
            if not job_id:
                logger.warning("警告：发现缺失 job_id 的记录，将跳过。")
                continue

            item_function = item.get('function') or item.get('category')  # 兼容可能的不同 key
            final_function = item_function if item_function else target_function

            record = (
                job_id,
                item.get('jobName'),
                item.get('industryType2Str'),
                item.get('jobDescribe'),
                final_function,  # 字段：function
                item.get('provideSalaryString'),  # 字段：salary (可能为 None)
                item.get('major1Str'),
                item.get('jobAreaCode'),  # 字段：provinceCode (可能为 None)
                current_timestamp  # 新增字段：processed_at
            )
            records_to_insert.append(record)

        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.executemany(insert_sql, records_to_insert)
            self.connection.commit()

            rows_affected = cursor.rowcount
            logger.info(f"尝试插入 {len(records_to_insert)} 条记录，实际成功入库 {rows_affected} 条。")
            return True, rows_affected
        except sqlite3.Error as e:
            logger.error(f"批量插入数据时出错: {e}")
            self.connection.rollback()
            return False, 0
        finally:
            self._disconnect()

    def update_processed_at(self, job_id: str, processed_time: Optional[str] = None) -> bool:
        """
        更新指定职位的 processed_at 字段。

        :param job_id: 职位ID
        :param processed_time: 处理时间，如果为 None 则使用当前时间
        :return: 更新成功返回 True，否则返回 False
        """
        if processed_time is None:
            processed_time = datetime.now().isoformat()

        update_sql = f"""
        UPDATE "{self.table_name}"
        SET processed_at = ?
        WHERE job_id = ?;
        """

        try:
            self._connect()
            cursor = self.connection.cursor()
            cursor.execute(update_sql, (processed_time, job_id))
            self.connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"成功更新职位 {job_id} 的 processed_at 字段为 {processed_time}")
                return True
            else:
                logger.warning(f"未找到职位 ID: {job_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"更新 processed_at 字段时出错: {e}")
            self.connection.rollback()
            return False
        finally:
            self._disconnect()

    def batch_update_processed_at(self, job_ids: List[str], processed_time: Optional[str] = None) -> int:
        """
        批量更新多个职位的 processed_at 字段。

        :param job_ids: 职位ID列表
        :param processed_time: 处理时间，如果为 None 则使用当前时间
        :return: 成功更新的记录数
        """
        if not job_ids:
            return 0

        if processed_time is None:
            processed_time = datetime.now().isoformat()

        update_sql = f"""
        UPDATE "{self.table_name}"
        SET processed_at = ?
        WHERE job_id = ?;
        """

        records = [(processed_time, job_id) for job_id in job_ids]

        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.executemany(update_sql, records)
            self.connection.commit()
            updated_count = cursor.rowcount
            logger.info(f"批量更新了 {updated_count} 条记录的 processed_at 字段")
            return updated_count
        except sqlite3.Error as e:
            logger.error(f"批量更新 processed_at 字段时出错: {e}")
            self.connection.rollback()
            return 0
        finally:
            self._disconnect()

    def get_random_job_by_function(self, function: str) -> Optional[Dict[str, Any]]:
        """
        根据指定的职能 (function) 随机返回一条职位数据。

        :param function: 职能分类字符串 (例如: 'Java开发', '产品经理')
        :return: 如果找到数据，返回包含字段信息的字典；如果没有找到或出错，返回 None
        """
        if not function:
            logger.error("错误：function 参数不能为空。")
            return None

        query_sql = f"""
        SELECT job_id, job_name, industry_type, job_description, function, salary, major, provinceCode, processed_at
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
                logger.warning(f"未找到职能为 '{function}' 的任何职位数据。")
                return None

        except sqlite3.Error as e:
            logger.error(f"随机查询职位时出错: {e}")
            return None
        finally:
            self._disconnect()

    def get_count_by_default_function(self) -> int:
        """
        返回数据库中 function 字段等于 self.default_function 的记录数量。

        :return: 记录数量，查询失败返回 0
        """
        query_sql = f"""
        SELECT COUNT(*) FROM "{self.table_name}"
        WHERE function = ?;
        """
        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query_sql, (self.default_function,))
            row = cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.Error as e:
            logger.error(f"统计 function='{self.default_function}' 的记录数量时出错: {e}")
            return 0
        finally:
            self._disconnect()

    def get_unprocessed_jobs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取尚未处理（processed_at 为 NULL）的职位记录。

        :param limit: 限制返回的记录数，如果为 None 则返回所有
        :return: 未处理的职位列表
        """
        query_sql = f"""
        SELECT job_id, job_name, industry_type, job_description, function, salary, major, provinceCode, processed_at
        FROM "{self.table_name}"
        WHERE processed_at IS NULL
        """

        if limit is not None:
            query_sql += f" LIMIT {limit};"
        else:
            query_sql += ";"

        self._connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query_sql)
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]

            logger.info(f"找到 {len(result)} 条未处理的记录")
            return result
        except sqlite3.Error as e:
            logger.error(f"查询未处理记录时出错: {e}")
            return []
        finally:
            self._disconnect()