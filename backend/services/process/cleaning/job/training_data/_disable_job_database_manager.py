# # backend/services/spider/platforms/job_51/public/_disable_job_database_manager.py
# import sqlite3
# from pathlib import Path
# from datetime import datetime
# from loguru import logger
# from typing import List, Dict, Any, Optional
#
# from backend.services.process.cleaning.public.base_database_manager import BaseDatabaseManager
#
#
# class JobDatabaseManager(BaseDatabaseManager):
#     """
#     专业解析后数据存储管理器。
#     使用固定表名 'parsed_jobs'，通过 major_name 字段区分不同专业的职位数据。
#     包含 processed_at 字段用于断点续传。
#     """
#
#     TABLE_NAME = "parsed_jobs"
#
#     # 定义需要动态添加的列 (用于旧表升级)
#     EXTRA_COLUMNS = {
#         "processed_at": "TEXT DEFAULT NULL"
#     }
#
#     def __init__(self, db_path: Path, major_name: str):
#         super().__init__(str(db_path))
#         self.major_name = major_name
#         # 初始化并升级表结构
#         self._initialize_schema()
#
#     def _initialize_schema(self):
#         """创建表、索引，并检查是否需要添加新列"""
#         # 1. 创建主表 (包含新字段)
#         create_table_sql = f"""
#         CREATE TABLE IF NOT EXISTS "{self.TABLE_NAME}" (
#             job_id TEXT NOT NULL,
#             major_name TEXT NOT NULL,
#             job_name TEXT,
#             industry_type TEXT,
#             job_description TEXT,
#             processed_at TEXT DEFAULT NULL,
#             PRIMARY KEY (job_id, major_name)
#         );
#         """
#         self.execute_update(create_table_sql)
#
#         # 2. 创建索引
#         indexes = [
#             f"CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_major ON \"{self.TABLE_NAME}\" (major_name);",
#             f"CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_job_id ON \"{self.TABLE_NAME}\" (job_id);",
#             # 关键索引：加速查询未处理数据
#             f"CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_status ON \"{self.TABLE_NAME}\" (major_name, processed_at);"
#         ]
#         for idx_sql in indexes:
#             self.execute_update(idx_sql)
#
#         # 3. 【重要】检查并添加缺失的列 (兼容旧数据库)
#         existing_columns = self._get_existing_columns()
#         for col_name, col_def in self.EXTRA_COLUMNS.items():
#             if col_name not in existing_columns:
#                 logger.info(f"检测到表 '{self.TABLE_NAME}' 缺少列 '{col_name}'，正在迁移...")
#                 alter_sql = f'ALTER TABLE "{self.TABLE_NAME}" ADD COLUMN "{col_name}" {col_def};'
#                 try:
#                     self.execute_update(alter_sql)
#                     logger.success(f"✅ 成功添加列: {col_name}")
#                 except sqlite3.Error as e:
#                     logger.error(f"❌ 添加列 {col_name} 失败: {e}")
#
#     def _get_existing_columns(self) -> List[str]:
#         """获取表中现有的列名列表"""
#         query = f"PRAGMA table_info(\"{self.TABLE_NAME}\");"
#         rows = self.execute_query(query)
#         return [row['name'] for row in rows]
#
#     def insert_parsed_data(self, parsed_data_list: List[Dict[str, Any]]) -> bool:
#         """
#         插入解析后的数据。新数据的 processed_at 默认为 NULL (未处理)。
#         """
#         if not parsed_data_list:
#             return True
#
#         insert_sql = f"""
#         INSERT OR IGNORE INTO "{self.TABLE_NAME}"
#             (job_id, major_name, job_name, industry_type, job_description)
#         VALUES (?, ?, ?, ?, ?);
#         """
#
#         records = []
#         for item in parsed_data_list:
#             job_id = item.get('jobId')
#             if not job_id:
#                 continue
#             records.append((
#                 job_id,
#                 self.major_name,
#                 item.get('jobName'),
#                 item.get('industryType2Str'),
#                 item.get('jobDescribe')
#             ))
#
#         if not records:
#             return True
#
#         try:
#             count = self.execute_update(insert_sql, records)  # 注意：executemany 需要特殊处理，这里简化为循环或修改父类支持 executemany
#             # 修正：父类 execute_update 只支持单条或需自行循环，这里为了简单使用循环调用或修改逻辑
#             # 更好的方式是直接操作 cursor，但为了保持架构一致，我们稍微调整一下策略：
#             # 由于父类 execute_update 设计为单次执行，这里我们手动处理批量插入
#             self._batch_insert(records, insert_sql)
#             logger.info(f"[{self.major_name}] 成功插入/忽略 {len(records)} 条数据。")
#             return True
#         except Exception as e:
#             logger.error(f"插入数据失败: {e}")
#             return False
#
#     def _batch_insert(self, records: List[tuple], sql: str):
#         """内部方法：执行批量插入"""
#         if not self.conn:
#             self._connect()
#         cursor = self.conn.cursor()
#         try:
#             cursor.executemany(sql, records)
#             self.conn.commit()
#         except Exception as e:
#             self.conn.rollback()
#             raise e
#         finally:
#             cursor.close()
#
#     # --- 状态管理方法 ---
#
#     def mark_as_processed(self, job_id: str) -> bool:
#         """标记指定 job_id 为已处理"""
#         sql = f"""
#         UPDATE "{self.TABLE_NAME}"
#         SET processed_at = ?
#         WHERE job_id = ? AND major_name = ?;
#         """
#         ts = datetime.now().isoformat()
#         return self.execute_update(sql, (ts, job_id, self.major_name)) > 0
#
#     def get_unprocessed_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
#         """获取未处理的数据列表"""
#         sql = f"""
#         SELECT job_id, job_name, job_description
#         FROM "{self.TABLE_NAME}"
#         WHERE major_name = ? AND processed_at IS NULL
#         LIMIT ?;
#         """
#         return self.execute_query(sql, (self.major_name, limit))
#
#     def get_pending_count(self) -> int:
#         """获取未处理数据数量"""
#         sql = f"SELECT COUNT(*) as c FROM \"{self.TABLE_NAME}\" WHERE major_name = ? AND processed_at IS NULL"
#         res = self.execute_query(sql, (self.major_name,))
#         return res[0]['c'] if res else 0
#
#     def reset_status(self) -> int:
#         """重置所有数据为未处理状态 (用于重跑)"""
#         sql = f"UPDATE \"{self.TABLE_NAME}\" SET processed_at = NULL WHERE major_name = ?"
#         return self.execute_update(sql, (self.major_name,))