import time

class SpiderUrlManager:
    def __init__(self, function: str):
        self.function = function
        self.DEGREE_ONLY_BACHELOR = "04"
        self.DEGREE_COMBINED = "03%2C04"
        self.degree = self.DEGREE_ONLY_BACHELOR   # 当前学历模式，可随时切换
        self.timestamp = int(time.time())
        self._build_url_part1()                   # 构建带时间戳的前缀
        self._build_static_parts()                # 构建静态部分（只需一次）

    def _build_url_part1(self):
        """根据当前时间戳重新构建 url_part_1"""
        self.url_part_1 = (
            f"https://we.51job.com/api/job/search-pc"
            f"?api_key=51job"
            f"&timestamp={self.timestamp}"
            f"&keyword="
            f"&searchType=2"
            f"&function="
        )

    def _build_static_parts(self):
        """构建不随时间和学历变化的 URL 片段（只需初始化一次）"""
        self.url_part_2 = (
            f"&industry="
            f"&jobArea="
            f"&jobArea2="
            f"&landmark="
            f"&metro="
            f"&salary="
            f"&workYear="
            f"&degree="
        )
        self.url_part_3 = (
            f"&companyType="
            f"&companySize="
            f"&jobType="
            f"&issueDate="
            f"&sortType=0"
            f"&pageNum="
        )
        self.url_part_4 = (
            f"&requestId="
            f"&pageSize=20"
            f"&source=1"
            f"&accountId="
            f"&pageCode=sou%7Csou%7Csoulb"
            f"&scene=7"
        )

    def refresh_timestamp(self):
        """更新时间戳并重建依赖时间戳的 url_part_1"""
        self.timestamp = int(time.time())
        self._build_url_part1()

    def set_degree_combined(self, combined: bool):
        """
        设置学历模式
        :param combined: True -> 大专+本科 (03%2C04) , False -> 仅本科 (04)
        """
        self.degree = self.DEGREE_COMBINED if combined else self.DEGREE_ONLY_BACHELOR

    def get_url(self, page_num: int) -> str:
        """基于当前的状态（时间戳、学历模式）生成 URL"""
        return f"{self.url_part_1}{self.function}{self.url_part_2}{self.degree}{self.url_part_3}{page_num}{self.url_part_4}"