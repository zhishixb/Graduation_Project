import json
from pathlib import Path
from typing import List, Optional, Dict, Any

class JSONLoader:
    """通用的 JSON 文件加载器（支持懒加载和缓存）"""
    def __init__(self, file_path: Path, lazy: bool = False):
        self.file_path = Path(file_path)
        self.lazy = lazy
        self._data: Optional[Any] = None

    def _load(self) -> Any:
        if not self.file_path.exists():
            raise FileNotFoundError(f"JSON 文件不存在: {self.file_path}")
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @property
    def data(self) -> Any:
        if self._data is None:
            self._data = self._load()
        return self._data

    def reload(self) -> None:
        self._data = self._load()

    def __repr__(self) -> str:
        return f"JSONLoader({self.file_path}, loaded={self._data is not None})"