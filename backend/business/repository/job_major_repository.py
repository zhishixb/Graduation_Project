import sqlite3
from pathlib import Path
from typing import List, Dict, Union


class JobMajorRepository:
    """用于查询 job_major_similarity 表的数据库接口。"""

    def __init__(self, db_path: Union[str, Path]):
        """
        初始化数据库连接。
        :param db_path: SQLite 数据库文件路径，可接受字符串或 pathlib.Path 对象
        """
        # 将路径统一转为字符串，兼容 Path 对象
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row  # 使结果能通过列名访问

    def get_top_functions_by_major(
        self, major_name: str, limit: int = 10
    ) -> List[Dict[str, Union[str, float]]]:
        """
        根据专业名称返回相似度最高的前 N 条岗位名称及相似度。
        :param major_name: 专业名称
        :param limit: 返回记录数，默认 10
        :return: 列表，元素为 {'function_name': str, 'similarity': float}
        """
        query = """
                SELECT function_name, similarity
                FROM job_major_similarity
                WHERE major_name = ?
                ORDER BY similarity DESC LIMIT ?
                """
        cursor = self.conn.execute(query, (major_name, limit))
        return [
            {"function_name": row["function_name"], "similarity": row["similarity"]}
            for row in cursor
        ]

    def get_top_majors_by_function(
        self, function_name: str, limit: int = 10
    ) -> List[Dict[str, Union[str, float]]]:
        """
        根据岗位名称返回相似度最高的前 N 条专业名称及相似度。
        :param function_name: 岗位名称
        :param limit: 返回记录数，默认 10
        :return: 列表，元素为 {'major_name': str, 'similarity': float}
        """
        query = """
                SELECT major_name, similarity
                FROM job_major_similarity
                WHERE function_name = ?
                ORDER BY similarity DESC LIMIT ?
                """
        cursor = self.conn.execute(query, (function_name, limit))
        return [
            {"major_name": row["major_name"], "similarity": row["similarity"]}
            for row in cursor
        ]

    def get_similarity(
            self, major_name: str, function_name: str
    ) -> Dict[str, Union[str, float]]:
        """
        根据专业名和岗位名查询唯一匹配的相似度分数。
        :param major_name: 专业名称
        :param function_name: 岗位名称
        :return: 字典 {'major_name': str, 'function_name': str, 'similarity': float}
                 若未找到则返回空字典 {}
        """
        query = """
                SELECT major_name, function_name, similarity
                FROM job_major_similarity
                WHERE major_name = ? \
                  AND function_name = ?
                """
        cursor = self.conn.execute(query, (major_name, function_name))
        row = cursor.fetchone()
        if row is None:
            return {}
        return {
            "major_name": row["major_name"],
            "function_name": row["function_name"],
            "similarity": row["similarity"],
        }

    def close(self):
        """关闭数据库连接。"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()