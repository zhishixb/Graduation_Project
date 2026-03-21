import time

class SpiderUrlManager:
    def __init__(self, function: str):
        self.timestamp = int(time.time())
        self.function = function

        self.url_part_1 = (
            f"https://we.51job.com/api/job/search-pc"
            f"?api_key=51job"
            f"&timestamp={self.timestamp}"
            f"&keyword="
            f"&searchType=2"
            f"&function="
        )
        self.url_part_2 = (
            f"&industry="
            f"&jobArea="
            f"&jobArea2="
            f"&landmark="
            f"&metro="
            f"&salary="
            f"&workYear="
            f"&degree=04"
            f"&companyType="
            f"&companySize="
            f"&jobType="
            f"&issueDate="
            f"&sortType=0"
            f"&pageNum="
        )
        self.url_part_3 = (
            f"&requestId="
            f"&pageSize=20"
            f"&source=1"
            f"&accountId="
            f"&pageCode=sou%7Csou%7Csoulb"  # 这里保持你原有的编码状态
            f"&scene=7"
        )

    def get_url(self, page_num: int) -> str:
        """
        通过拼接 prefix + page_num + suffix 生成最终 URL。
        这样保证了 pageNum 出现在原本的位置，且没有重复参数。
        """
        return f"{self.url_part_1}{self.function}{self.url_part_2}{page_num}{self.url_part_3}"