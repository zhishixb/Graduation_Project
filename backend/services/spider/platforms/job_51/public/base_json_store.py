import json, os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

class BaseJsonStore:
    """
    【基类】提供通用的 JSON 文件原子读写、备份机制。
    不包含任何具体业务逻辑。
    """
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.backup_path = self.file_path.with_suffix(self.file_path.suffix + '.bak')
        self.data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if not self.file_path.exists():
            self.data = {}
            self._save_internal()
            return
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except json.JSONDecodeError:
            if self.backup_path.exists():
                with open(self.backup_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                raise ValueError(f"文件损坏且无备份：{self.file_path}")

    def _save_internal(self):
        if self.file_path.exists():
            os.replace(self.file_path, self.backup_path)
        temp_path = self.file_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.file_path)
            if self.backup_path.exists():
                self.backup_path.unlink()
        except Exception as e:
            if self.backup_path.exists():
                os.replace(self.backup_path, self.file_path)
            raise IOError(f"保存失败：{e}")

    def save(self):
        self._save_internal()

    def __enter__(self): return self
    def __exit__(self, *args):
        self.save()
        return False