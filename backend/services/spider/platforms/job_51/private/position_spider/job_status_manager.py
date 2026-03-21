from pathlib import Path
from typing import Any, Dict

from backend.services.spider.platforms.job_51.public.base_json_store import BaseJsonStore


class JobStatusManager(BaseJsonStore):
    """
    【业务类】管理层级化职位状态 (学科->子类->职位)。
    继承自 BaseJsonStore，自动处理原子写入和备份。
    """

    def __init__(self, file_path: Path, category: str, sub_category: str, position: str):
        """
        :param file_path: JSON 文件路径 (由外部注入，避免硬编码)
        :param category: 大类 (e.g., "销售/客服")
        :param sub_category: 中类 (e.g., "销售管理")
        :param position: 职位 (e.g., "销售经理")
        """
        super().__init__(str(file_path))

        self.category = category
        self.sub_category = sub_category
        self.position = position

        # 验证路径是否存在，如果不存在则抛出异常或初始化
        if not self._path_exists():
            raise KeyError(
                f"数据路径不存在: '{category}' -> '{sub_category}' -> '{position}'\n"
                f"请检查 JSON 文件或先初始化数据结构。"
            )

    def _get_node(self) -> Dict[str, Any]:
        """
        获取当前职位对应的数据节点引用。
        注意：返回的是 self.data 的引用，修改它会直接修改内存中的数据。
        """
        try:
            return self.data[self.category][self.sub_category][self.position]
        except KeyError:
            # 理论上 __init__ 已经检查过，但为了安全再次检查
            raise KeyError(f"内存中未找到路径: {self.category} -> {self.sub_category} -> {self.position}")

    def _path_exists(self) -> bool:
        """检查三级路径是否在数据中存在"""
        try:
            _ = self.data[self.category][self.sub_category][self.position]
            return True
        except KeyError:
            return False

    # --- 业务操作方法 ---

    def get_count(self) -> int:
        """获取当前计数值"""
        return self._get_node().get("count", 0)

    def get_state(self) -> str:
        """获取当前状态"""
        return self._get_node().get("state", "unknown")

    def is_pending(self) -> bool:
        """判断是否处于 pending 状态"""
        return self.get_state() == "pending"

    def update_count(self, new_count: int, auto_save: bool = True):
        """
        更新计数值
        :param auto_save: 是否立即触发保存 (默认为 True)
        """
        node = self._get_node()
        node["count"] = new_count
        if auto_save:
            self.save()

    def increment_count(self, step: int = 1, auto_save: bool = True):
        """
        增加计数值 (原子操作在内存中，保存由 auto_save 控制)
        """
        node = self._get_node()
        current = node.get("count", 0)
        node["count"] = current + step
        if auto_save:
            self.save()

    def set_state_completed(self, auto_save: bool = True):
        """标记为完成"""
        node = self._get_node()
        node["state"] = "completed"
        if auto_save:
            self.save()

    def get_id(self) -> str:
        """获取职位 ID"""
        return self._get_node().get("id", "")