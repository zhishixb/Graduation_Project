import re
from typing import List, Set, Dict


class MedicalMajorExtractor:
    """
    从医学类专业描述文本中提取：
    - 书名号《》内的课程名称
    - “部分高校按以下专业方向培养：”后的专业方向列表

    新增功能：自动将文本中的英文逗号 ',' 替换为中文逗号 '，' 以统一格式。
    """

    def __init__(self):
        # 预编译正则表达式，提升性能
        self.course_pattern = re.compile(r'《([^》]+)》')
        self.direction_prefix_pattern = re.compile(
            r'[，,。；;]?\s*部分高校按以下专业方向培养[：:]\s*'
        )
        # 预编译替换用的正则（虽然 str.replace 更快，但正则可用于更复杂的场景，这里直接用 str.replace 即可）

    def _normalize_text(self, text: str) -> str:
        """
        文本预处理：将英文逗号替换为中文逗号。
        也可以在此处添加其他标准化逻辑（如全角转半角等）。
        """
        if not text:
            return text
        # 核心修改：替换英文逗号为中文逗号
        return text.replace(',', '，')

    def extract_courses(self, text: str) -> List[str]:
        """
        提取所有《》中的课程名，去重并保持顺序。
        """
        # 先标准化文本
        normalized_text = self._normalize_text(text)

        matches = self.course_pattern.findall(normalized_text)
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
        # 先标准化文本
        normalized_text = self._normalize_text(text)

        # 查找“部分高校...”的位置
        match = self.direction_prefix_pattern.search(normalized_text)
        if not match:
            return []

        # 从匹配位置之后截取剩余字符串
        suffix = normalized_text[match.end():].strip()

        # 如果后面有句号/分号/换行等，只取到第一个句子结束
        # 注意：因为已经替换过逗号，这里主要看句号等结束符
        sentence_end = re.search(r'[。；;\n]', suffix)
        if sentence_end:
            suffix = suffix[:sentence_end.start()]

        # 按常见分隔符分割：顿号、中文逗号（英文逗号已转为中文）、空格、斜杠等
        # 现在正则里其实可以只留 '，'，但保留 ',' 以防万一有漏网之鱼也无害
        parts = re.split(r'[、，,\s/]+', suffix)

        directions = []
        for part in parts:
            part = part.strip()
            if part:
                directions.append(part)

        return directions

    def extract_all(self, text: str) -> Dict[str, List[str]]:
        """
        同时提取课程和专业方向，返回结构化字典。
        """
        # 可以在这里统一做一次 normalize，然后传给内部方法，
        # 或者像上面那样在每个子方法里做。为了灵活性，上面采用了子方法内处理。
        # 如果希望全局一次处理，可以这样写：
        normalized_text = self._normalize_text(text)

        return {
            "courses": self._extract_courses_from_normalized(normalized_text),
            "directions": self._extract_directions_from_normalized(normalized_text)
        }

    # 内部辅助方法，直接接收已标准化的文本，避免重复替换
    def _extract_courses_from_normalized(self, text: str) -> List[str]:
        matches = self.course_pattern.findall(text)
        seen: Set[str] = set()
        unique_courses = []
        for course in matches:
            course = course.strip()
            if course and course not in seen:
                unique_courses.append(course)
                seen.add(course)
        return unique_courses

    def _extract_directions_from_normalized(self, text: str) -> List[str]:
        match = self.direction_prefix_pattern.search(text)
        if not match:
            return []

        suffix = text[match.end():].strip()
        sentence_end = re.search(r'[。；;\n]', suffix)
        if sentence_end:
            suffix = suffix[:sentence_end.start()]

        # 此时文本中已无英文逗号，主要按中文顿号和逗号分割
        parts = re.split(r'[、，\s/]+', suffix)

        directions = []
        for part in parts:
            part = part.strip()
            if part:
                directions.append(part)
        return directions


# ================== 测试用例 ==================
if __name__ == "__main__":
    extractor = MedicalMajorExtractor()

    # 模拟包含英文逗号的文本
    test_text = """
    主要课程：《内科学》,《外科学》,《妇产科学》。
    部分高校按以下专业方向培养：临床心理学，医学影像学，康复医学, 精神医学。
    """

    print("原始文本片段：")
    print(test_text)
    print("-" * 30)

    result = extractor.extract_all(test_text)

    print("提取结果：")
    print(f"课程列表: {result['courses']}")
    print(f"专业方向: {result['directions']}")

    # 验证英文逗号是否被正确处理
    # 预期：课程列表中不应包含逗号，专业方向列表应正确分割 "康复医学" 和 "精神医学"