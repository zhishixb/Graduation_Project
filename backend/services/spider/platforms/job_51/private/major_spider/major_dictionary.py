import json
from pathlib import Path
from typing import Any, Dict


class MajorDictionary:
    """
    爬虫运行状态存储类（已更新支持三级结构：学科->二级学科->专业）。
    自动基于当前文件位置管理 JSON 文件。
    """

    def __init__(self):
        """
        初始化存储类。
        """
        # 核心：获取当前文件所在的绝对路径
        # 假设此文件位于 project/utils/store.py，则向上找4层到项目根目录
        current_file_path = Path(__file__).resolve().parent.parent.parent.parent.parent

        # 构建完整的 JSON 文件路径
        self.file_path = current_file_path / 'data' / 'json' / '51job_major_status.json'

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

    def set_major_state(self, category: str, secondary_category: str, major_name: str, state: int = 2) -> bool:
        """
        【新增功能】给定一级学科、二级学科和专业名，将其 state 改为指定值。
        适配结构: { "学科": { "二级学科": { "专业名": { "state": ... } } } }

        :param category: 一级学科名 (例如: "理学", "工学")
        :param secondary_category: 二级学科/专业类名 (例如: "数学类", "计算机类")
        :param major_name: 专业名 (例如: "数学与应用数学", "软件工程")
        :param state: 目标状态值 (例如: 2)
        :return: 是否成功找到并修改
        """
        data = self._read_data()

        # 1. 检查一级学科是否存在
        if category not in data:
            print(f"❌ 未找到一级学科: {category}")
            return False

        secondary_dict = data[category]

        # 2. 检查二级学科是否存在
        if secondary_category not in secondary_dict:
            print(f"❌ 在学科 '{category}' 下未找到二级学科: {secondary_category}")
            return False

        major_dict = secondary_dict[secondary_category]

        # 3. 检查并修改具体专业
        if major_name not in major_dict:
            print(f"❌ 在 '{category}' -> '{secondary_category}' 下未找到专业: {major_name}")
            return False

        # 修改状态
        major_dict[major_name]["state"] = state

        # 写回文件
        return self._write_data(data)