import json
import re
from pathlib import Path
from typing import List, Dict, Set, Union


class SkillExtractor:
    """从文本中提取预定义技能词"""

    def __init__(self, skills_file: Union[str, Path] = "skills.json"):
        self.skills_file = Path(skills_file)
        self.skills: List[str] = []
        self.skill_category_map: Dict[str, str] = {}  # 技能 -> 分类
        self._load_skills()
        self.pattern, self.skill_map = self._build_pattern(self.skills)

    def _load_skills(self):
        """从 JSON 文件中提取技能词及对应分类，去重并保序"""
        with open(self.skills_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        seen_skills = set()
        for category in data.get("skills", []):
            cat_name = category.get("category", "")
            for skill in category.get("skills", []):
                if skill not in seen_skills:
                    seen_skills.add(skill)
                    self.skills.append(skill)
                    self.skill_category_map[skill] = cat_name

    def _build_pattern(self, skills: List[str]):
        """构建正则模式，按长度降序排列，忽略大小写"""
        sorted_skills = sorted(skills, key=len, reverse=True)

        skill_map: Dict[str, str] = {}  # 小写 -> 原始技能名
        escaped_parts = []
        for s in sorted_skills:
            escaped = re.escape(s)
            escaped_parts.append(escaped)
            skill_map[s.lower()] = s

        pattern_str = r"(?<![a-zA-Z0-9])(?:" + "|".join(escaped_parts) + r")(?![a-zA-Z0-9])"
        return re.compile(pattern_str, re.IGNORECASE), skill_map

    def extract_from_text(self, text: str) -> List[str]:
        """从单条文本中提取技能词（去重，保留原始标准名称）"""
        if not isinstance(text, str) or not text.strip():
            return []
        matches = self.pattern.findall(text)
        seen: Set[str] = set()
        result = []
        for m in matches:
            standard = self.skill_map.get(m.lower(), m)
            if standard not in seen:
                seen.add(standard)
                result.append(standard)
        return result

    def extract_skills_grouped_by_category(self, text: str) -> Dict[str, List[str]]:
        """
        从文本中提取技能词，并按分类归类，返回：
        {
            "编程语言": ["Python", "Java"],
            "Web框架": ["Django", "Spring"],
            ...
        }
        """
        skill_list = self.extract_from_text(text)
        grouped = {}
        for skill in skill_list:
            category = self.skill_category_map.get(skill, "未分类")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(skill)
        return grouped

    def extract_skills_and_categories(self, text: str) -> Dict[str, List[str]]:
        """
        从文本提取技能词及其所属分类，返回：
        {
            "skills": ["Python", "Django", ...],
            "categories": ["编程语言", "编程语言常用库/框架", ...]
        }
        分类列表去重，顺序与技能首次出现顺序一致。
        """
        skill_list = self.extract_from_text(text)
        categories = []
        seen_cat = set()
        for skill in skill_list:
            cat = self.skill_category_map.get(skill, "未分类")
            if cat not in seen_cat:
                seen_cat.add(cat)
                categories.append(cat)
        return {"skills": skill_list, "categories": categories}

    def extract_from_texts(self, texts: List[str]) -> List[List[str]]:
        """批量提取，返回每条文本对应的技能词列表"""
        return [self.extract_from_text(text) for text in texts]