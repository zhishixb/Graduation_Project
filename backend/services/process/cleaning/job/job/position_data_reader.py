# 适合云算力的全量内存处理版本 - 适配 position_jobs 表
import sqlite3
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from loguru import logger
from datetime import datetime

from backend.services.process.cleaning.public.base_database_manager import BaseDatabaseManager


class PositionDataReader(BaseDatabaseManager):
    """
    涉及数据库：position_jobs 表
    用于清洗数据时和数据库的交互（针对多线程/内存预加载优化版）
    适配表结构：job_id, job_name, industry_type, job_description, function, salary, major, provinceCode, processed_at
    """

    TABLE_NAME = "position_jobs"

    def __init__(self, db_path: Path):
        super().__init__(str(db_path))

        logger.debug(f"初始化全局职位读取器（position_jobs）：{db_path}")

        # --- 性能优化关键代码 ---
        # 1. 关闭同步模式 (大幅提升 UPDATE 速度)
        # 默认是 FULL，每次写入都要等待磁盘确认。设为 OFF 后速度提升数倍。
        # 风险：仅在电脑突然断电时可能丢失最后几秒数据，程序崩溃不影响。
        try:
            self.conn.execute("PRAGMA synchronous = OFF;")
            self.conn.execute("PRAGMA journal_mode = MEMORY;")
            logger.debug("SQLite 性能优化已应用 (synchronous=OFF, journal_mode=MEMORY)")
        except Exception as e:
            logger.warning(f"SQLite 优化设置失败: {e}")

    # --- 内存预加载支持 ---

    def get_all_pending_data(self, function_filter: Optional[str] = None,
                             major_filter: Optional[str] = None) -> List[
        Tuple[str, str, str, Optional[str], Optional[str]]]:
        """
        【核心方法】一次性获取所有待处理数据到内存。

        :param function_filter: 可选，按职能分类过滤（例如只处理 'Java开发'）
        :param major_filter: 可选，按专业过滤
        :return: List[(job_id, job_description, function, salary, major), ...]
                 注意：job_description 是清洗的主要对象
        """
        sql = f"""
        SELECT job_id, job_description, function, salary, major, job_name, industry_type, provinceCode
        FROM "{self.TABLE_NAME}" 
        WHERE processed_at IS NULL
        """

        # 添加过滤条件
        conditions = []
        params = []

        if function_filter:
            conditions.append("function = ?")
            params.append(function_filter)

        if major_filter:
            conditions.append("major = ?")
            params.append(major_filter)

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        try:
            rows = self.execute_query(sql, tuple(params) if params else None)
            if not rows:
                logger.info("没有待处理的数据")
                return []

            # 转换为元组列表，方便多线程解包
            # 返回核心字段：job_id, job_description, function, salary, major
            return [
                (
                    row['job_id'],  # 用于后续更新
                    row['job_description'],  # 需要清洗的主要内容
                    row['function'],  # 职能分类（可能用于清洗策略）
                    row['salary'],  # 薪资信息（可能用于清洗）
                    row['major'],  # 专业（可能用于清洗策略）
                    row['job_name'],  # 职位名称（辅助信息）
                    row['industry_type'],  # 行业类型（辅助信息）
                    row['provinceCode']  # 省份代码（辅助信息）
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"全量读取数据失败: {e}")
            return []

    def get_all_pending_data_dict(self, function_filter: Optional[str] = None,
                                  major_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        【核心方法】一次性获取所有待处理数据到内存（字典格式）。
        与 get_all_pending_data 类似，但返回字典，便于通过字段名访问。

        :param function_filter: 可选，按职能分类过滤
        :param major_filter: 可选，按专业过滤
        :return: List[Dict]，每个字典包含所有字段
        """
        sql = f"""
        SELECT job_id, job_name, industry_type, job_description, function, salary, major, provinceCode
        FROM "{self.TABLE_NAME}" 
        WHERE processed_at IS NULL
        """

        conditions = []
        params = []

        if function_filter:
            conditions.append("function = ?")
            params.append(function_filter)

        if major_filter:
            conditions.append("major = ?")
            params.append(major_filter)

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        try:
            rows = self.execute_query(sql, tuple(params) if params else None)
            if not rows:
                logger.info("没有待处理的数据")
                return []

            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"全量读取数据失败: {e}")
            return []

    def batch_mark_processed(self, job_ids: List[str], processed_time: Optional[str] = None) -> int:
        """
        【核心方法】批量标记为已处理。
        使用 SQL IN 语句一次性更新，避免多线程频繁锁库。

        :param job_ids: 待更新的 ID 列表
        :param processed_time: 处理时间，如果为 None 则使用当前时间
        :return: 受影响的行数
        """
        if not job_ids:
            return 0

        if processed_time is None:
            processed_time = datetime.now().isoformat()

        # 构造 (?, ?, ?, ...) 占位符
        placeholders = ','.join('?' * len(job_ids))

        sql = f"""
        UPDATE "{self.TABLE_NAME}" 
        SET processed_at = ? 
        WHERE job_id IN ({placeholders});
        """

        # 参数：(当前时间, id1, id2, ...)
        params = [processed_time] + job_ids

        try:
            return self.execute_update(sql, params)
        except Exception as e:
            logger.error(f"批量更新状态失败: {e}")
            return 0

    def batch_mark_processed_with_condition(self, job_ids: List[str],
                                            function_filter: Optional[str] = None,
                                            processed_time: Optional[str] = None) -> int:
        """
        【扩展方法】带条件过滤的批量标记。
        防止误更新（例如更新时确保职能分类匹配）。

        :param job_ids: 待更新的 ID 列表
        :param function_filter: 可选，确保只更新特定职能的数据
        :param processed_time: 处理时间
        :return: 受影响的行数
        """
        if not job_ids:
            return 0

        if processed_time is None:
            processed_time = datetime.now().isoformat()

        placeholders = ','.join('?' * len(job_ids))

        sql = f"""
        UPDATE "{self.TABLE_NAME}" 
        SET processed_at = ? 
        WHERE job_id IN ({placeholders})
        """

        params = [processed_time] + job_ids

        if function_filter:
            sql += " AND function = ?"
            params.append(function_filter)

        try:
            return self.execute_update(sql, params)
        except Exception as e:
            logger.error(f"带条件批量更新状态失败: {e}")
            return 0

    # --- 🛠️ 辅助方法 ---

    def get_all_pending_ids(self, function_filter: Optional[str] = None,
                            major_filter: Optional[str] = None) -> List[str]:
        """
        获取所有待处理任务的 ID 列表。
        用于 tqdm 进度条计算总数（如果不使用内存预加载模式）。

        :param function_filter: 可选，按职能过滤
        :param major_filter: 可选，按专业过滤
        :return: job_id 列表
        """
        sql = f"""
        SELECT job_id 
        FROM "{self.TABLE_NAME}" 
        WHERE processed_at IS NULL
        """

        conditions = []
        params = []

        if function_filter:
            conditions.append("function = ?")
            params.append(function_filter)

        if major_filter:
            conditions.append("major = ?")
            params.append(major_filter)

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        try:
            cursor = self.conn.execute(sql, tuple(params) if params else None)
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取待处理 ID 列表失败: {e}")
            return []

    def get_stats(self, function_filter: Optional[str] = None,
                  major_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息（支持按职能/专业过滤）

        :param function_filter: 可选，按职能过滤
        :param major_filter: 可选，按专业过滤
        :return: 统计字典
        """
        # 构建 WHERE 条件
        conditions = []
        params = []

        if function_filter:
            conditions.append("function = ?")
            params.append(function_filter)

        if major_filter:
            conditions.append("major = ?")
            params.append(major_filter)

        # ✅ 修复：正确构建 WHERE 子句
        # 总数查询的 WHERE 子句
        total_where = ""
        if conditions:
            total_where = "WHERE " + " AND ".join(conditions)

        # 待处理查询的 WHERE 子句（需要加上 processed_at IS NULL）
        pending_conditions = conditions.copy()
        pending_conditions.append("processed_at IS NULL")
        pending_where = "WHERE " + " AND ".join(pending_conditions)

        total_sql = f'SELECT COUNT(*) as c FROM "{self.TABLE_NAME}" {total_where}'
        pending_sql = f'SELECT COUNT(*) as c FROM "{self.TABLE_NAME}" {pending_where}'

        total_res = self.execute_query(total_sql, tuple(params) if params else None)
        pending_res = self.execute_query(pending_sql, tuple(params) if params else None)

        total = total_res[0]['c'] if total_res else 0
        pending = pending_res[0]['c'] if pending_res else 0

        result = {
            "total": total,
            "pending": pending,
            "processed": total - pending
        }

        # 添加过滤信息
        if function_filter:
            result["function_filter"] = function_filter
        if major_filter:
            result["major_filter"] = major_filter

        return result

    def get_pending_by_function(self, function: str) -> List[Tuple[str, str]]:
        """
        获取特定职能的所有待处理职位（轻量级版本，只返回 ID 和描述）

        :param function: 职能分类
        :return: List[(job_id, job_description)]
        """
        sql = f"""
        SELECT job_id, job_description 
        FROM "{self.TABLE_NAME}" 
        WHERE function = ? AND processed_at IS NULL
        """

        try:
            rows = self.execute_query(sql, (function,))
            return [(row['job_id'], row['job_description']) for row in rows]
        except Exception as e:
            logger.error(f"获取职能 '{function}' 的待处理数据失败: {e}")
            return []

    def get_pending_by_major(self, major: str) -> List[Tuple[str, str]]:
        """
        获取特定专业的所有待处理职位（轻量级版本）

        :param major: 专业名称
        :return: List[(job_id, job_description)]
        """
        sql = f"""
        SELECT job_id, job_description 
        FROM "{self.TABLE_NAME}" 
        WHERE major = ? AND processed_at IS NULL
        """

        try:
            rows = self.execute_query(sql, (major,))
            return [(row['job_id'], row['job_description']) for row in rows]
        except Exception as e:
            logger.error(f"获取专业 '{major}' 的待处理数据失败: {e}")
            return []

    def reset_processed_status(self, job_ids: List[str]) -> int:
        """
        【应急方法】重置指定职位的处理状态（将 processed_at 设为 NULL）。
        用于需要重新处理某些数据时的场景。

        :param job_ids: 需要重置的职位 ID 列表
        :return: 受影响的行数
        """
        if not job_ids:
            return 0

        placeholders = ','.join('?' * len(job_ids))
        sql = f"""
        UPDATE "{self.TABLE_NAME}" 
        SET processed_at = NULL 
        WHERE job_id IN ({placeholders});
        """

        try:
            return self.execute_update(sql, job_ids)
        except Exception as e:
            logger.error(f"重置处理状态失败: {e}")
            return 0

    def get_function_list(self) -> List[str]:
        """
        获取所有不同的职能分类

        :return: 职能列表
        """
        sql = f'SELECT DISTINCT function FROM "{self.TABLE_NAME}" WHERE function IS NOT NULL ORDER BY function'

        try:
            rows = self.execute_query(sql)
            return [row['function'] for row in rows]
        except Exception as e:
            logger.error(f"获取职能列表失败: {e}")
            return []

    def get_major_list(self) -> List[str]:
        """
        获取所有不同的专业

        :return: 专业列表
        """
        sql = f'SELECT DISTINCT major FROM "{self.TABLE_NAME}" WHERE major IS NOT NULL ORDER BY major'

        try:
            rows = self.execute_query(sql)
            return [row['major'] for row in rows]
        except Exception as e:
            logger.error(f"获取专业列表失败: {e}")
            return []