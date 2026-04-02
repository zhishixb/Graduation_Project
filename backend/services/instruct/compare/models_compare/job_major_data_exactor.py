from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.services.process.cleaning.job.public.csv_manager import MajorCourseFinder
from backend.services.process.cleaning.job.public._disable_job_description_parser import JobDescriptionParser
from backend.services.spider.platforms.job_51.private.position_spider.dao import JobDatabaseManager


class JobMajorDataExactor:
    """
    职位数据提取器。
    负责从数据库中提取特定职能的职位描述数据，并支持带来源标记的清洗。
    """

    def __init__(self, db_path: Path, csv_path: Path, default_function: str = "通用职能"):
        """
        初始化提取器。

        :param db_path: 数据库文件的绝对或相对路径 (Path 对象)
        :param default_function: 传递给 JobDatabaseManager 的默认职能参数
        """
        if isinstance(db_path, str):
            db_path = Path(db_path)

        self.db_manager = JobDatabaseManager(db_path, default_function=default_function)
        self.data_cleaner = JobDescriptionParser()
        self.job_detail_exactor = MajorCourseFinder(csv_path)

    def get_major_detail(self, major_name: str) -> str:
        return self.job_detail_exactor.get_courses(major_name)

    def get_cleaned_requirements_by_functions(self, function_list: List[str]) -> List[Dict[str, str]]:
        """
        根据职能列表获取描述，清洗后，【关键修改】：将每个职能的所有要求合并为一段完整文本。

        :param function_list: 职能名称列表
        :return: 列表，元素为字典：{'function': '职能名', 'requirement': '合并后的完整要求文本'}
                 长度将与 function_list 保持一致（或等于数据库中找到的职能数量）。
        """
        raw_data_with_func = self.get_job_descriptions_with_function(function_list)

        if not raw_data_with_func:
            print(f"警告：未从数据库中找到职能 {function_list} 的任何数据。")
            return []

        all_cleaned_requirements = []

        # 用于去重或聚合：{ "职能名": ["要求1", "要求2", ...] }
        func_requirements_map: Dict[str, List[str]] = {}

        print(f"开始清洗 {len(raw_data_with_func)} 条职位描述...")

        for i, item in enumerate(raw_data_with_func):
            func_name = item['function']
            desc_text = item['job_description']

            # 获取该条描述的所有要求列表 (例如: ['要求A', '要求B', ...])
            reqs_list = self.data_cleaner.get_requirements_text(desc_text, clean=True)

            # 初始化列表如果不存在
            if func_name not in func_requirements_map:
                func_requirements_map[func_name] = []

            # 将提取出的要求加入该职能的列表
            func_requirements_map[func_name].extend(reqs_list)

        # 【关键修改】：将列表合并为字符串，确保每个职能只输出一条记录
        for func_name, req_list in func_requirements_map.items():
            if not req_list:
                continue

            # 使用换行符将所有要求拼接成一个大字符串
            # 例如: "要求1\n要求2\n要求3..."
            merged_text = "\n".join(req_list)

            all_cleaned_requirements.append({
                "function": func_name,
                "requirement": merged_text  # 👈 这里是合并后的长字符串，而不是单条要求
            })

        print(f"✅ 清洗完成：输入 {len(function_list)} 个职能，输出 {len(all_cleaned_requirements)} 条合并后的文本。")

        return all_cleaned_requirements

    def get_job_descriptions_with_function(self, function_list: List[str]) -> List[Dict[str, Any]]:
        """
        内部辅助方法：获取职位描述时，同时保留对应的 function 字段。

        :param function_list: 职能列表
        :return: [{'function': '...', 'job_description': '...'}, ...]
        """
        results = []

        if not function_list:
            return results

        for func in function_list:
            if not func or not isinstance(func, str):
                continue

            job_data = self.db_manager.get_random_job_by_function(func)

            if job_data and job_data.get('job_description'):
                results.append({
                    "function": func,
                    "job_description": job_data['job_description'],
                    # 可选：也可以带上 job_id 或其他信息以便追踪
                    # "job_id": job_data.get('job_id')
                })
            else:
                # 静默跳过或记录日志
                pass

        return results