from urllib.parse import quote

class UrlManager:
    def __init__(self, major: str):
        self.major = major
        self.suffix = [
            "专业就业情况",
            "专业怎么样",
        ]

    def get_url(self, index: int) -> str:
        keyword = self.major + self.suffix[index]
        encoded_keyword = quote(keyword)
        url = (
            f"https://www.xiaohongshu.com/search_result"
            f"?keyword={encoded_keyword}&source=web_explore_feed"
        )
        return url

    def get_note_url(self, note_id: str, xsec_token: str) -> str:
        url = (
            f"https://www.xiaohongshu.com/explore/{note_id}"
            f"?xsec_token={xsec_token}&xsec_source=pc_search&source=web_explore_feed"
        )
        return url