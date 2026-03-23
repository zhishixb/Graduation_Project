from pathlib import Path
from typing import Optional


class MajorCourseFinder:
    def __init__(self, csv_path: str):
        """
        初始化课程查找器，加载专业数据。
        :param csv_path: major_data.csv 文件路径
        """
        self.major_to_courses = {}
        self._load_data(csv_path)

    def _load_data(self, csv_path: str):
        """
        从 CSV 文件加载 专业 -> 专业介绍 的映射
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 按英文逗号分割，最多分成1部分（防止文本中有）
                parts = line.split(",", 1)

                major_name = parts[0].strip()
                major_courses_field = parts[1].strip()  # 如 "主要课程：大学物理、..."

                # 提取“主要课程：”后面的内容
                if major_courses_field.startswith("主要课程："):
                    courses = major_courses_field[len("主要课程："):].strip()
                    self.major_to_courses[major_name] = courses
                else:
                    # 兼容异常情况
                    self.major_to_courses[major_name] = major_courses_field

    def get_courses(self, major_name: str) -> Optional[str]:
        """
        根据专业名称获取主要课程列表字符串。
        :param major_name: 专业名称
        :return: 主要课程字符串
        """
        return self.major_to_courses.get(major_name)