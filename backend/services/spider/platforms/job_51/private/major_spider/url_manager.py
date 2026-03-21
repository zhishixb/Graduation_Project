from urllib.parse import quote
import time

class SpiderUrlManager:
    def __init__(self, job_name: str):
        self.job_name = job_name
        # 1. 只在初始化时编码一次关键词
        self.encoded_keyword = quote(job_name, safe='')
        # 2. 只在初始化时生成一次时间戳（代表这次搜索会话的开始时间）
        self.timestamp = int(time.time())

        # 3. 预构造好“不变”的 URL 前半部分和固定参数
        self.url_prefix = (
            f"https://we.51job.com/api/job/search-pc"
            f"?api_key=51job"
            f"&timestamp={self.timestamp}"
            f"&keyword={ self.encoded_keyword}"
            f"&searchType=2"
            f"&function="
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
        self.url_suffix = (
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
        return f"{self.url_prefix}{page_num}{self.url_suffix}"