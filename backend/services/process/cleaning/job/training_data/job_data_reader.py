from typing import Iterator, Optional
from loguru import logger
from backend.services.process.cleaning.public.base_database_manager import BaseDatabaseManager


class JobDataReader(BaseDatabaseManager):
    """
    职位描述读取器
    """

    def __init__(self, db_path: str, major_name: str):
        super().__init__(db_path)
        self.table_name = major_name

        # 更严格的表名校验 (只允许字母、数字、下划线、中文)
        import re
        if not re.match(r"^[\w\u4e00-\u9fa5]+$", major_name):
            raise ValueError(f"Invalid table name: {major_name}")

    def get_descriptions(self) -> Iterator[Optional[str]]:
        """
        流式生成器：逐条产出 job_description
        注意：调用者需要确保在使用完生成器后调用 reader.close()
        """
        # 构建 SQL (表名无法参数化，必须拼接，但已做过校验)
        sql = f'SELECT job_description FROM "{self.table_name}"'

        try:
            # 直接使用父类的流式方法
            # 不需要 with self，因为连接已经在 __init__ 中建立
            for row in self.execute_stream_query(sql):
                desc = row.get('job_description')
                # 过滤掉 None 或空字符串 (可选)
                if desc is not None:
                    yield desc.strip() if isinstance(desc, str) else desc
        except Exception as e:
            logger.error(f"读取 {self.table_name} 描述失败：{e}")
            raise
        # 注意：这里不要调用 self.close()！
        # 因为生成器可能被外部 break 或提前停止，导致 close 无法执行。
        # 应该由控制该 Reader 生命周期的代码 (如 Controller) 来调用 close()。