import csv
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List
from loguru import logger


class MajorVectorLookup:
    """
    加载专业名称与向量的 CSV 文件到内存，支持根据专业名称快速获取向量。
    CSV 格式：专业名称,向量（逗号分隔的浮点数）
    """

    def __init__(self, csv_path: Path):
        """
        :param csv_path: 包含“专业名称”和“向量”列的 CSV 文件路径
        """
        self.csv_path = csv_path
        self._vectors: Dict[str, np.ndarray] = {}
        self._load()

    def _load(self) -> None:
        """加载 CSV 文件到内存字典"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # 校验列名（可选）
            if reader.fieldnames != ['专业名称', '向量']:
                logger.warning(f"CSV 列名应为 ['专业名称', '向量']，实际为 {reader.fieldnames}")

            for row in reader:
                name = row.get('专业名称', '').strip()
                vector_str = row.get('向量', '').strip()
                if not name or not vector_str:
                    continue
                try:
                    # 将逗号分隔的字符串转为 numpy 数组
                    vec = np.array([float(x) for x in vector_str.split(',')], dtype=np.float32)
                    self._vectors[name] = vec
                except ValueError as e:
                    logger.error(f"解析专业 '{name}' 的向量失败: {e}")

        logger.info(f"已加载 {len(self._vectors)} 个专业向量")

    def get_vector(self, major_name: str) -> Optional[np.ndarray]:
        """
        根据专业名称获取对应的向量。
        :param major_name: 专业名称
        :return: numpy 数组，若不存在则返回 None
        """
        return self._vectors.get(major_name)

    def has_major(self, major_name: str) -> bool:
        """检查专业是否存在"""
        return major_name in self._vectors

    def get_all_majors(self) -> List[str]:
        """返回所有已加载的专业名称列表"""
        return list(self._vectors.keys())

    def get_all_vectors(self) -> Dict[str, np.ndarray]:
        """返回整个专业-向量的字典（引用）"""
        return self._vectors