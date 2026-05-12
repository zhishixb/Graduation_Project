import json
from pathlib import Path
from typing import Dict, Any

class JobListRepository:
    def __init__(self, file_path: Path):
        self._file_path = file_path

    def get_raw_data(self) -> Dict[str, Any]:
        """读取整个 JSON 文件并返回 Python 字典"""
        with self._file_path.open("r", encoding="utf-8") as f:
            return json.load(f)