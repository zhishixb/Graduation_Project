import json
from pathlib import Path
from typing import Optional


class MajorToCategoryFinder:
    """
    根据专业名称（major_name）查找其所属的一级学科门类。
    """

    def __init__(self, json_path: Path):
        """
        加载 JSON 文件并构建映射表。

        :param json_path: 51job_major_status.json 文件路径
        """
        self.major_to_category: dict[str, str] = {}
        self._load_mapping(json_path)

    def _load_mapping(self, json_path: Path) -> None:
        """递归遍历 JSON 结构，提取每个专业的 major_name 及其所属一级键"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for category, sub_dict in data.items():
            # 二级：专业类（如 "哲学类"）
            for sub_category, major_dict in sub_dict.items():
                # 三级：具体专业（如 "逻辑学"）
                for major_code, major_info in major_dict.items():
                    # 只有包含 "major_name" 字段的才是有效专业
                    if 'major_name' in major_info:
                        major_name = major_info['major_name']
                        # 避免覆盖（理论上专业名唯一，但若重复则保留首次出现的分类）
                        if major_name not in self.major_to_category:
                            self.major_to_category[major_name] = category
                        # 可选：打印警告处理重复
                        # else:
                        #     print(f"警告：专业名 '{major_name}' 重复，已存在分类 '{self.major_to_category[major_name]}'，忽略新分类 '{category}'")

    def get_category(self, major_name: str) -> Optional[str]:
        """
        根据专业名称获取所属的一级学科门类。

        :param major_name: 专业名称（如 "计算机科学与技术"）
        :return: 一级学科门类（如 "工学"），如果未找到则返回 None
        """
        return self.major_to_category.get(major_name)

    def get_all_majors(self) -> list[str]:
        """返回所有已加载的专业名称列表"""
        return list(self.major_to_category.keys())


# 使用示例
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    default_csv_path = project_root / 'data' / 'json' / '51job_major_status.json'

    finder = MajorToCategoryFinder(default_csv_path)

    # 测试几个专业
    test_majors = ["逻辑学", "计算机科学与技术", "经济学", "护理学", "不存在的专业"]
    for major in test_majors:
        category = finder.get_category(major)
        print(f"{major} -> {category if category else '未找到'}")