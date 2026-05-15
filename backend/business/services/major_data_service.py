# services/major_data_service.py
import csv
import re
from pathlib import Path
from typing import Dict, Optional, List

from backend.business.models.schemas import MajorIntroChunk
from backend.business.models.exceptions import ConfigFileNotFoundError, MajorNotFoundError
from backend.business.repository.major_repository import MajorRepository


class MajorDataService:
    """提供专业介绍查询与解析服务"""

    def __init__(self, csv_path: Path, major_repo: Optional[MajorRepository] = None):
        """
        :param csv_path: major_data.csv 的文件路径
        :param major_repo: 可选的数据库仓库实例，用于查询热度等数据
        """
        self._csv_path = csv_path
        self._major_repo = major_repo
        self._major_dict: Optional[Dict[str, str]] = None  # 缓存：{专业名称: 介绍原文}

    def _load_data(self) -> Dict[str, str]:
        """从 CSV 文件加载全部专业数据，构建字典"""
        if not self._csv_path.exists():
            raise ConfigFileNotFoundError(f"专业数据文件不存在：{self._csv_path}")

        major_dict = {}
        # utf-8-sig 自动处理 BOM 字符
        with self._csv_path.open('r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # 跳过标题行 (专业名称,专业介绍)
            for row in reader:
                if len(row) >= 2:
                    name = row[0].strip()
                    desc = row[1].strip()
                    if name:  # 忽略空名称
                        major_dict[name] = desc
        return major_dict

    def get_intro_by_major(self, major_name: str) -> str:
        """
        根据专业名称返回完整介绍文本。
        :raises MajorNotFoundError: 专业不存在
        """
        if self._major_dict is None:
            self._major_dict = self._load_data()

        intro = self._major_dict.get(major_name)
        if intro is None:
            raise MajorNotFoundError(f"未找到专业 '{major_name}' 的介绍")
        return intro

    @staticmethod
    def parse_intro_to_chunk(intro_text: str) -> MajorIntroChunk:
        """
        将介绍文本拆分为结构化字段。
        就业发展方向取自“专业描述”字段句号后的内容。
        """
        # 第一步：按分号提取主要课程、培养方向、专业描述（原始）
        patterns = {
            "main_courses": r"主要课程：([^；]*)",
            "training_direction": r"培养方向：([^；]*)",
            "description_raw": r"专业描述：([^；]*)",
        }

        extracted = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, intro_text)
            extracted[field] = match.group(1).strip() if match else ""

        # 第二步：从专业描述中拆分出 description 和 employment_direction
        desc_raw = extracted.pop("description_raw")
        if '。' in desc_raw:
            # 按第一个句号分割
            parts = desc_raw.split('。', 1)
            description = parts[0].strip()
            employment = parts[1].strip()
        else:
            description = desc_raw
            employment = ""

        return MajorIntroChunk(
            main_courses=extracted.get("main_courses", ""),
            training_direction=extracted.get("training_direction", ""),
            description=description,
            employment_direction=employment
        )

    def get_intro_chunks_by_major(self, major_name: str) -> MajorIntroChunk:
        """
        获取某专业的结构化介绍信息。
        :raises MajorNotFoundError: 专业不存在
        """
        full_intro = self.get_intro_by_major(major_name)
        return self.parse_intro_to_chunk(full_intro)

    def get_hot_majors(self, limit: int = 30) -> List[Dict[str, object]]:
        """返回热度最高的前 N 条专业名称及热度值"""
        if self._major_repo is None:
            raise RuntimeError("MajorRepository 未注入，无法查询热度数据")
        return self._major_repo.get_top_majors_by_heat(limit)