from loguru import logger
from typing import Dict, Generator, Optional, Any, List
from pathlib import Path
from backend.services.process.cleaning.public.base_database_manager import BaseDatabaseManager


class MajorDatabaseManager(BaseDatabaseManager):
    """
    专门用于管理高考专业数据的数据库类。
    支持断点续传：通过检查 extracted_skills 字段是否为空来判断进度。
    """

    TABLE_NAME = "majors"
    RESULT_COLUMN = "extracted_skills"

    def __init__(self, db_path: Path):
        # 将 Path 对象转为字符串传给父类（sqlite3 需要 str）
        super().__init__(str(db_path))
        logger.debug(f"初始化专业数据库管理器：{db_path}")

        # 初始化时确保结构正确
        self.ensure_result_column()

    def ensure_result_column(self):
        """确保 majors 表中有 extracted_skills 字段"""
        check_query = f"PRAGMA table_info({self.TABLE_NAME})"
        try:
            columns = self.execute_query(check_query)
            column_names = [col['name'] for col in columns]

            if self.RESULT_COLUMN not in column_names:
                logger.warning(f"表 {self.TABLE_NAME} 缺少字段 '{self.RESULT_COLUMN}'，正在自动添加...")
                alter_query = f"ALTER TABLE {self.TABLE_NAME} ADD COLUMN {self.RESULT_COLUMN} TEXT;"
                self.execute_update(alter_query)
                logger.success(f"✅ 成功添加字段 '{self.RESULT_COLUMN}'，支持断点续传。")
            else:
                logger.debug(f"ℹ️  字段 '{self.RESULT_COLUMN}' 已存在。")
        except Exception as e:
            logger.error(f"❌ 检查或添加字段失败：{e}")
            raise e

    def check_table_exists(self) -> bool:
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        try:
            result = self.execute_query(query, (self.TABLE_NAME,))
            return len(result) > 0
        except Exception as e:
            logger.error(f"检查表状态失败：{e}")
            return False

    def get_major_count(self, only_pending: bool = False) -> int:
        if only_pending:
            query = f"""
                SELECT COUNT(*) as count 
                FROM {self.TABLE_NAME} 
                WHERE {self.RESULT_COLUMN} IS NULL OR trim({self.RESULT_COLUMN}) = ''
            """
        else:
            query = f"SELECT COUNT(*) as count FROM {self.TABLE_NAME}"

        try:
            rows = self.execute_query(query)
            return rows[0]["count"] if rows else 0
        except Exception as e:
            logger.error(f"统计数量失败：{e}")
            return 0

    def stream_majors(self, limit: Optional[int] = None) -> Generator[Dict[str, Optional[str]], None, None]:
        base_query = f"""
            SELECT special_id, name, is_what, learn_what 
            FROM {self.TABLE_NAME} 
            WHERE {self.RESULT_COLUMN} IS NULL 
               OR trim({self.RESULT_COLUMN}) = ''
        """

        if limit:
            base_query += " LIMIT ?"
            params = (limit,)
        else:
            params = ()

        try:
            for row in self.execute_stream_query(base_query, params):
                yield {
                    "special_id": row["special_id"],
                    "name": row["name"],
                    "is_what": row["is_what"],
                    "learn_what": row["learn_what"]
                }
        except Exception as e:
            logger.error(f"流式读取未处理的专业数据失败：{e}")
            raise e

    def reset_processed_results(self) -> int:
        """
        重置所有已处理的数据。
        将 extracted_skills 字段设为 NULL，以便重新清洗。
        返回被重置的行数。
        """
        query = f"""
            UPDATE {self.TABLE_NAME} 
            SET {self.RESULT_COLUMN} = NULL 
            WHERE {self.RESULT_COLUMN} IS NOT NULL 
              AND trim({self.RESULT_COLUMN}) != ''
        """
        try:
            rows_affected = self.execute_update(query)
            logger.warning(f"🔄 已重置 {rows_affected} 条已处理的专业数据，准备重新清洗。")
            return rows_affected
        except Exception as e:
            logger.error(f"❌ 重置数据失败：{e}")
            raise e

    def get_major_by_id(self, special_id: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE special_id = ?"
        try:
            rows = self.execute_query(query, (special_id,))
            return dict(rows[0]) if rows else None
        except Exception as e:
            logger.error(f"查询专业 ID {special_id} 失败：{e}")
            return None

    def update_skills_result(self, special_id: str, skills_json: str) -> bool:
        query = f"UPDATE {self.TABLE_NAME} SET {self.RESULT_COLUMN} = ? WHERE special_id = ?"
        try:
            rows_affected = self.execute_update(query, (skills_json, special_id))
            if rows_affected > 0:
                logger.debug(f"💾 已保存结果到 ID: {special_id}")
                return True
            else:
                logger.warning(f"⚠️ 更新 ID {special_id} 时未影响任何行")
                return False
        except Exception as e:
            logger.error(f"❌ 更新技能结果失败 (ID: {special_id}): {e}")
            return False

    def get_processed_count(self) -> int:
        """获取已处理的数量"""
        total = self.get_major_count(only_pending=False)
        pending = self.get_major_count(only_pending=True)
        return total - pending