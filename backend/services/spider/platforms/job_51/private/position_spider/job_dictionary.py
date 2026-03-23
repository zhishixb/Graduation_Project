import json
from pathlib import Path
from typing import Any, Dict


class JobDictionary :
    def __init__(self):
        """
        初始化存储类。
        """
        # 核心：获取当前文件所在的绝对路径
        # 假设此文件位于 project/utils/store.py，则向上找4层到项目根目录
        current_file_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent

        # 构建完整的 JSON 文件路径
        self.file_path = current_file_path / 'data' / 'json' / '51job_job_data.json'

    def _read_data(self) -> Dict[str, Any]:
        """内部方法：读取 JSON 文件内容。"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️ 读取状态文件出错 ({self.file_path.name}): {e}")
            return {}

    def _write_data(self, data: Dict[str, Any]) -> bool:
        """内部方法：将数据写入 JSON 文件。"""
        try:
            # 确保目录存在
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"❌ 写入状态文件失败: {e}")
            return False

    def get_all_state(self) -> Dict[str, Any]:
        """
        【核心需求】全量返回 JSON 文件内容。
        :return: 包含所有状态键值对的字典。
        """
        return self._read_data()

