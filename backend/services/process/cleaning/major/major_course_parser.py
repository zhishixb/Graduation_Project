import re
from typing import List, Set

class MedicalMajorExtractor:
    """
    从医学类专业描述文本中提取：
    - 书名号《》内的课程名称
    - “部分高校按以下专业方向培养：”后的专业方向列表
    """

    def __init__(self):
        # 预编译正则表达式，提升性能
        self.course_pattern = re.compile(r'《([^》]+)》')
        self.direction_prefix_pattern = re.compile(
            r'[，,。；;]?\s*部分高校按以下专业方向培养[：:]\s*'
        )

    def extract_courses(self, text: str) -> List[str]:
        """
        提取所有《》中的课程名，去重并保持顺序。
        """
        matches = self.course_pattern.findall(text)
        # 去重但保留顺序
        seen: Set[str] = set()
        unique_courses = []
        for course in matches:
            course = course.strip()
            if course and course not in seen:
                unique_courses.append(course)
                seen.add(course)
        return unique_courses

    def extract_directions(self, text: str) -> List[str]:
        """
        提取“部分高校按以下专业方向培养：”之后的专业方向。
        支持多种分隔符：顿号、逗号、空格、换行等。
        """
        # 查找“部分高校...”的位置
        match = self.direction_prefix_pattern.search(text)
        if not match:
            return []

        # 从匹配位置之后截取剩余字符串
        suffix = text[match.end():].strip()

        # 如果后面有句号/分号/换行等，只取到第一个句子结束
        sentence_end = re.search(r'[。；;\n]', suffix)
        if sentence_end:
            suffix = suffix[:sentence_end.start()]

        # 按常见分隔符分割：顿号、逗号、空格、斜杠等
        parts = re.split(r'[、，,\s/]+', suffix)
        directions = []
        for part in parts:
            part = part.strip()
            if part:
                directions.append(part)

        return directions

    def extract_all(self, text: str) -> dict:
        """
        同时提取课程和专业方向，返回结构化字典。
        """
        return {
            "courses": self.extract_courses(text),
            "directions": self.extract_directions(text)
        }