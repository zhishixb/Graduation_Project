import csv
from pathlib import Path
from typing import Dict, Optional, List, Union


class CsvRowReader:
    """
    读取格式为 'major_name,cleaned_requirements' 的 CSV 文件。
    初始化时一次性加载所有行到内存，提供迭代器逐行返回字典。
    """

    def __init__(self, file_path: Union[str, Path], expected_headers: List[str] = None):
        """
        :param file_path: CSV 文件路径
        :param expected_headers: 期望的表头列表，默认为 ['major_name', 'cleaned_requirements']
        """
        self.file_path = Path(file_path)
        self.expected_headers = expected_headers or ['major_name', 'cleaned_requirements']
        self.rows: List[Dict[str, str]] = []
        self._index = 0
        self._load()

    def _load(self) -> None:
        """加载 CSV 文件到内存"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            # 校验列名
            if reader.fieldnames != self.expected_headers:
                raise ValueError(f"CSV 表头应为 {self.expected_headers}，实际为 {reader.fieldnames}")
            self.rows = list(reader)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> Dict[str, str]:
        if self._index >= len(self.rows):
            raise StopIteration
        row = self.rows[self._index]
        self._index += 1
        return row

    def get_row(self, idx: int) -> Optional[Dict[str, str]]:
        """按索引获取指定行（从0开始）"""
        if 0 <= idx < len(self.rows):
            return self.rows[idx]
        return None

    def reset(self) -> None:
        """重置迭代器位置"""
        self._index = 0

    def length(self) -> int:
        """返回总行数"""
        return len(self.rows)

    def all_rows(self) -> List[Dict[str, str]]:
        """返回所有行的列表（拷贝）"""
        return self.rows.copy()