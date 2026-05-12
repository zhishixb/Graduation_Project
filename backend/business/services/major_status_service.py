# services/major_status_service.py
import json
from pathlib import Path
from typing import Dict, Any

class MajorStatusService:
    def __init__(self, file_path: Path):
        self.file_path = file_path  # 现在是 Path 对象

    def get_all_major_status(self) -> Dict[str, Any]:
        data = json.loads(self.file_path.read_text(encoding='utf-8'))
        return data