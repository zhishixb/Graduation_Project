from DrissionPage import ChromiumPage, ChromiumOptions
from pathlib import Path
from urllib.parse import quote
import json
import time

from backend.services.spider.platforms.xhs.url_manager import UrlManager


class XHSSpider:
    """小红书搜索+评论采集器"""

    # 常量配置
    SEARCH_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes'
    COMMENT_API = 'https://edith.xiaohongshu.com/api/sns/web/v2/comment/page'

    def __init__(
        self,
        major: str,
        user_data_dir: str,
        target_note_count: int = 20,
        search_scroll_times: int = 10,
        comment_max_scroll: int = 10,
        max_comments_per_note: int = None,
        headless: bool = False
    ):
        """
        :param major: 专业名
        :param user_data_dir: 浏览器用户数据目录路径
        :param target_note_count: 每个关键词希望采集的笔记数量
        :param search_scroll_times: 搜索页最大滚动次数
        :param comment_max_scroll: 详情页评论最大滚动次数
        :param max_comments_per_note: 每篇笔记最多采集的评论数，None 表示不限制
        :param headless: 是否无头模式
        """
        self.major = major
        self.url_manager = UrlManager(major)
        self.user_data_dir = user_data_dir
        self.target_note_count = target_note_count
        self.search_scroll_times = search_scroll_times
        self.comment_max_scroll = comment_max_scroll
        self.max_comments_per_note = max_comments_per_note
        self.headless = headless

        self.page = None
        self._init_browser()

    def _init_browser(self):
        """初始化浏览器页面"""
        options = ChromiumOptions()
        options.set_paths(user_data_path=str(self.user_data_dir))
        if self.headless:
            options.headless(True)
        self.page = ChromiumPage(options)

    def quit(self):
        """关闭浏览器"""
        if self.page:
            self.page.quit()

    # ==================== 搜索页相关 ====================
    def _process_search_response(self, packet, page_num: int):
        """解析搜索 API 响应，返回 items 列表"""
        response_data = packet.response.body
        if isinstance(response_data, dict):
            json_data = response_data
        elif isinstance(response_data, bytes):
            json_data = json.loads(response_data.decode('utf-8'))
        else:
            json_data = json.loads(response_data)

        items = json_data.get('data', {}).get('items', [])
        print(f"   📦 第 {page_num} 页 | 获取 {len(items)} 条记录")
        return items

    def _extract_note_info(self, items: list):
        """从原始 items 中提取笔记 id、xsec_token 并组装详情页 URL"""
        notes = []
        for item in items:
            if item.get('model_type') != 'note':
                continue
            note_id = item.get('id')
            xsec_token = item.get('xsec_token')
            if note_id and xsec_token:
                url = self.url_manager.get_note_url(note_id, xsec_token)
                notes.append({
                    'id': note_id,
                    'xsec_token': xsec_token,
                    'url': url
                })
        return notes

    def search_notes(self, index: int):
        """
        根据关键词搜索笔记，返回笔记列表（id、xsec_token、url）
        """
        print(f"\n开始搜索")

        url = self.url_manager.get_url(index)

        self.page.listen.start(self.SEARCH_API)
        self.page.get(url)
        time.sleep(1.5)

        print("🧹 清空监听缓存...")
        self.page.listen.clear()

        # 筛选操作：最多评论
        try:
            filter_btn = self.page.ele('text=筛选', timeout=5)
            if filter_btn:
                filter_btn.hover()
                most_comment_btn = self.page.wait.ele_displayed('text=最多评论', timeout=10)
                most_comment_btn.click()
                self.page.wait(1)
                collapse_btn = self.page.ele('text=收起', timeout=3)
                if collapse_btn:
                    collapse_btn.click()
            print("   ✅ 筛选完成（最多评论）")
        except Exception as e:
            print(f"   ⚠️ 筛选操作失败（可能无筛选按钮）: {e}")

        print(" 等待首次搜索 API 响应...")
        packet = self.page.listen.wait(timeout=15)
        if not packet:
            print("❌ 未捕获到搜索请求")
            self.page.listen.stop()
            return []

        all_items = []
        items = self._process_search_response(packet, 1)
        all_items.extend(items)

        # 滚动获取更多笔记
        for i in range(self.search_scroll_times):
            current_note_count = len(self._extract_note_info(all_items))
            if current_note_count >= self.target_note_count:
                break

            print(f"   ⬇️ 执行第 {i+1} 次滚动...")
            self.page.listen.clear()
            self.page.scroll.to_bottom()
            time.sleep(2)

            new_packet = self.page.listen.wait(timeout=3)
            if new_packet:
                items = self._process_search_response(new_packet, i+2)
                all_items.extend(items)
            else:
                print("      ⚠️ 未捕获到新响应，跳过本次滚动")

        self.page.listen.stop()
        notes = self._extract_note_info(all_items)[:self.target_note_count]
        print(f"   ✅ 搜索完成，共获取 {len(notes)} 条笔记")
        return notes

    # ==================== 评论采集相关 ====================
    def _extract_comments_data(self, comment_api_response: dict):
        """从评论 API 响应中提取主评论和子评论的 content 与 like_count"""
        data = comment_api_response.get('data', {})
        comments = data.get('comments', [])
        extracted = []
        for cmt in comments:
            main = {
                'content': cmt.get('content', ''),
                'like_count': cmt.get('like_count', '0')
            }
            sub_comments = cmt.get('sub_comments', [])
            main['sub_comments'] = [
                {
                    'content': sub.get('content', ''),
                    'like_count': sub.get('like_count', '0')
                }
                for sub in sub_comments
            ]
            extracted.append(main)
        return extracted

    def crawl_comments(self, note_url: str, max_comments: int = None):
        """
        访问笔记详情页，滚动评论区容器，采集评论（支持数量上限）
        :param note_url: 笔记 URL
        :param max_comments: 最大评论条数，默认 None 表示不限制
        """
        print(f"   🌐 访问笔记: {note_url[:80]}...")
        self.page.get(note_url)
        time.sleep(3)

        # 关闭可能的弹窗
        try:
            close_btn = self.page.ele('xpath://div[contains(@class,"close")]', timeout=2)
            if close_btn:
                close_btn.click()
        except:
            pass

        # 定位评论区滚动容器
        scroller = self.page.ele('.note-scroller', timeout=5)
        if not scroller:
            print("      ⚠️ 未找到滚动容器 .note-scroller，使用页面滚动作为降级")
            scroller = self.page

        # 滚动触发首次评论请求
        scroller.scroll.down(500)
        time.sleep(2)

        self.page.listen.start(self.COMMENT_API)
        self.page.listen.clear()

        all_comments = []

        for i in range(self.comment_max_scroll):
            print(f"⬇️ 执行第 {i+1} 次评论滚动...")
            scroller.scroll.to_bottom()
            time.sleep(2.5)

            packet = self.page.listen.wait(timeout=5)
            if not packet:
                print("⚠️ 未捕获到评论请求，尝试继续滚动...")
                self.page.listen.clear()
                continue

            response_data = packet.response.body
            if isinstance(response_data, bytes):
                response_data = json.loads(response_data.decode('utf-8'))
            elif isinstance(response_data, str):
                response_data = json.loads(response_data)

            data = response_data.get('data', {})
            has_more = data.get('has_more', False)
            extracted = self._extract_comments_data(response_data)
            all_comments.extend(extracted)

            print(f"📄 本页获取 {len(extracted)} 条评论 | 累计 {len(all_comments)} 条")

            # 检查是否达到上限
            if max_comments is not None and len(all_comments) >= max_comments:
                all_comments = all_comments[:max_comments]
                print(f"🎯 已达到评论上限 {max_comments} 条，停止采集")
                break

            if not has_more:
                print("✅ 所有评论已加载完毕")
                break

            self.page.listen.clear()

        self.page.listen.stop()
        return all_comments

    def run(
            self,
            crawl_comments: bool = True,
            note_interval: float = 2.0,
            output_dir: str = None,
            skip_existing: bool = True
    ):
        """
        执行采集：对 major 预设的多个关键词变体分别搜索，
        每轮结果保存到独立文件。若文件已存在且 skip_existing=True，则跳过该轮。
        """
        total_rounds = 3

        if output_dir is None:
            output_dir = Path(self.user_data_dir).parent
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        all_results = []

        for round_idx in range(total_rounds, 0, -1):
            round_filename = output_dir / f"{self.major}_round_{round_idx}_results.json"

            # 检查文件是否存在，若存在且需要跳过，则跳过本轮
            if skip_existing and round_filename.exists():
                print(f"⏭️ 文件 {round_filename} 已存在，跳过第 {round_idx} 轮采集")
                continue

            print(f"\n{'=' * 50}")
            print(f"🚀 开始第 {round_idx} 轮搜索 (major: {self.major})")
            print('=' * 50)

            notes = self.search_notes(round_idx)
            if not notes:
                print(f"⚠️ 第 {round_idx} 轮未获取到笔记，跳过保存")
                continue

            if crawl_comments:
                for idx, note in enumerate(notes, 1):
                    print(f"\n   --- 笔记 {idx}/{len(notes)} ---")
                    comments = self.crawl_comments(note['url'], max_comments=self.max_comments_per_note)
                    note['comments'] = comments
                    time.sleep(note_interval)

            round_result = {
                'major': self.major,
                'round': round_idx,
                'notes': notes
            }
            all_results.append(round_result)

            with open(round_filename, 'w', encoding='utf-8') as f:
                json.dump(round_result, f, ensure_ascii=False, indent=2)
            print(f"✅ 第 {round_idx} 轮结果已保存至: {round_filename}")

        return all_results