from pathlib import Path
from typing import Iterator, Optional

from backend.services.process.cleaning.job.public.base_database_manager import BaseDatabaseManager


# 假设 BaseDatabaseManager 已导入
# from .db_manager import BaseDatabaseManager

class JobDataReader(BaseDatabaseManager):
    """
    职位描述读取器
    利用父类的流式能力，实现内存高效的逐条读取。
    """

    def __init__(self, db_path: str, major_name: str):
        super().__init__(db_path)
        self.table_name = major_name

    def get_descriptions(self) -> Iterator[Optional[str]]:
        """
        流式生成器：逐条产出 job_description
        """
        # 安全性校验：防止 SQL 注入表名
        if '"' in self.table_name or ';' in self.table_name:
            raise ValueError("Invalid table name")

        # 构建 SQL
        sql = f'SELECT job_description FROM "{self.table_name}"'

        # 使用 'with self' 确保连接自动打开和关闭
        # 使用 'yield from' 直接委托给父类的流式方法
        with self:
            # execute_stream_query 返回的是一个迭代器
            # 我们在这里进行简单的字段提取转换
            for row in self.execute_stream_query(sql):
                # row 是 sqlite3.Row 对象，可以直接用列名访问
                yield row['job_description']