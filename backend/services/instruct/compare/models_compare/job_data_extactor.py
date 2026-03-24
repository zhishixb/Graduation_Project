from pathlib import Path
from typing import List, Optional
# 请确保导入路径正确，指向你的 JobDatabaseManager 类所在位置
from backend.services.spider.platforms.job_51.public.job_database_manager import JobDatabaseManager


class JobDataExactor:
    """
    职位数据提取器。
    负责从数据库中提取特定职能的职位描述数据。
    初始化时只需提供数据库路径，内部会自动管理数据库连接对象。
    """

    def __init__(self, db_path: Path, default_function: str = "通用职能"):
        """
        初始化提取器。

        :param db_path: 数据库文件的绝对或相对路径 (Path 对象)
        :param default_function: 传递给 JobDatabaseManager 的默认职能参数 (占位用)
        """
        # 确保传入的是 Path 对象
        if isinstance(db_path, str):
            db_path = Path(db_path)

        # 内部初始化数据库管理器
        self.db_manager = JobDatabaseManager(db_path, default_function=default_function)

    def get_job_descriptions_by_functions(self, function_list: List[str]) -> List[str]:
        """
        根据给定的职能列表，批量获取对应的职位描述 (job_description)。

        逻辑说明：
        1. 遍历输入的 function_list。
        2. 对每个 function，从数据库中随机抽取一条该职能的职位数据。
        3. 提取其中的 job_description 字段。
        4. 如果某个 function 没有找到数据，则跳过。

        :param function_list: 职能名称列表，例如 ['Java开发', 'Python开发', '产品经理']
        :return: 职位描述字符串列表。
        """
        descriptions = []

        if not function_list:
            return descriptions

        for func in function_list:
            if not func or not isinstance(func, str):
                continue

            # 调用内部管理器的随机查询方法
            job_data = self.db_manager.get_random_job_by_function(func)

            if job_data and job_data.get('job_description'):
                descriptions.append(job_data['job_description'])
            else:
                # 可选：记录警告
                # print(f"警告：未在数据库中找到职能 '{func}' 的相关职位描述，已跳过。")
                pass

        return descriptions

    def get_job_details_by_functions(self, function_list: List[str]) -> List[dict]:
        """
        (扩展方法) 返回包含完整信息的字典列表，而不仅仅是描述。

        :param function_list: 职能名称列表
        :return: 包含职位详细信息的字典列表
        """
        details = []

        for func in function_list:
            if not func:
                continue

            job_data = self.db_manager.get_random_job_by_function(func)

            if job_data:
                details.append(job_data)

        return details

    def close(self):
        """
        显式关闭数据库连接（如果需要）。
        通常 JobDatabaseManager 会在每次操作后自动断开，但保留此方法以备长生命周期使用。
        """
        if hasattr(self.db_manager, '_disconnect'):
            self.db_manager._disconnect()