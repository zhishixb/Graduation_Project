# backend/src/graduation_project/service/spider/core/spider_status.py
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class SpiderRunSignal:
    """
    用于在 JobSpider 和 UI 之间传递状态更新信息的数据类。
    """
    type: int # 0开始 1过程 2结束
    current_job: str
    current_page: int
    current_count: int
    target_count: int

    def to_mes(self) -> str:
        """
        将当前实例转换为消息字符串。
        """
        # ✅ 使用 f-string 进行格式化
        return f"正在爬取 {self.current_job}，进度：{self.current_count}/{self.target_count}"

    def to_dict(self) -> dict:
        """
        将当前实例转换为字典。
        这个方法封装了序列化逻辑，便于与前端通信。
        """
        return asdict(self)