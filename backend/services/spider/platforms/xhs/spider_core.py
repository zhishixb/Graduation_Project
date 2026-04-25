from DrissionPage import ChromiumPage, ChromiumOptions
import json
import time
from pathlib import Path
from typing import Union


class XHSSpiderCore:
    """小红书搜索+评论采集器（纯浏览器操作，不内置 URL 构造逻辑）"""

    # 常量配置
    SEARCH_API = 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes'
    COMMENT_API = 'https://edith.xiaohongshu.com/api/sns/web/v2/comment/page'

    def __init__(
        self,
        user_data_dir: Union[str, Path],
        target_note_count: int = 20,
        search_scroll_times: int = 10,
        comment_max_scroll: int = 10,
        headless: bool = False
    ):
        """
        :param user_data_dir: 浏览器用户数据目录路径（支持字符串或 Path 对象）
        :param target_note_count: 期望采集的笔记数量
        :param search_scroll_times: 搜索页最大滚动次数
        :param comment_max_scroll: 详情页评论最大滚动次数
        :param headless: 是否无头模式
        """
        # 统一转换为 Path 对象，再转为字符串保存
        self.user_data_dir = str(Path(user_data_dir))
        self.target_note_count = target_note_count
        self.search_scroll_times = search_scroll_times
        self.comment_max_scroll = comment_max_scroll
        self.headless = headless

        self.page = None
        self._init_browser()

    def _init_browser(self):
        """初始化浏览器页面"""
        options = ChromiumOptions()
        options.set_paths(user_data_path=self.user_data_dir)  # 已是字符串
        options.set_argument('--blink-settings=imagesEnabled=true')
        # options.set_pref('profile.managed_default_content_settings.images', 2)
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
        """
        从原始 items 中提取笔记 id 和 xsec_token
        返回列表：[{'id': note_id, 'xsec_token': xsec_token}, ...]
        """
        notes = []
        for item in items:
            if item.get('model_type') != 'note':
                continue
            note_id = item.get('id')
            xsec_token = item.get('xsec_token')
            if note_id and xsec_token:
                notes.append({
                    'id': note_id,
                    'xsec_token': xsec_token
                })
        return notes

    def search_notes(self, search_url: str) -> list:
        """
        访问给定的搜索 URL，滚动加载并返回笔记列表

        :param search_url: 小红书搜索结果页完整 URL（含关键词、排序等参数）
        :return: 笔记列表，每个元素为 dict，包含 id、xsec_token
        """
        print(f"\n🔍 开始搜索: {search_url[:100]}...")

        self.page.listen.start(self.SEARCH_API)
        self.page.get(search_url)
        time.sleep(1.5)

        print("🧹 清空监听缓存...")
        self.page.listen.clear()

        # 筛选操作：最多评论（若页面支持）
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

        print("⏳ 等待首次搜索 API 响应...")
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

    def crawl_comments(self, note_url: str, max_comments: int = None) -> list:
        """
        访问笔记详情页，滚动加载并采集评论数据

        :param note_url: 笔记详情页完整 URL
        :param max_comments: 最大评论条数，默认 None 表示不限制
        :return: 评论列表
        """
        print(f"🌐 访问笔记: {note_url[:80]}...")

        # 1. 在访问页面前启动监听（捕获首次加载的数据）
        self.page.listen.start(self.COMMENT_API)
        time.sleep(2)
        self.page.get(note_url)
        time.sleep(2)

        # 2. 关闭可能的弹窗
        try:
            close_btn = self.page.ele('xpath://div[contains(@class,"close")]', timeout=2)
            if close_btn:
                close_btn.click()
        except:
            pass

        # 3. 定位评论区滚动容器
        scroller = self.page.ele('.note-scroller', timeout=5)
        if not scroller:
            print("⚠️ 未找到滚动容器 .note-scroller，使用页面滚动作为降级")
            scroller = self.page

        # ------------------------------------------------------------
        # 新增：在进入 while 循环前检测“暂无评论”元素
        # ------------------------------------------------------------
        no_comments_el = self.page.ele('css:p.no-comments-text', timeout=3)
        if no_comments_el:
            print("⚠️ 该笔记暂无评论（检测到 .no-comments-text），结束采集")
            self.page.listen.stop()
            return []

        all_comments = []

        while len(all_comments) < (max_comments or float('inf')):
            # --- 获取一批评论数据 ---
            packet = self.page.listen.wait(timeout=5)
            if not packet:
                # 尝试滚动一次，看能否触发新数据
                scroller.scroll.to_bottom()
                time.sleep(2)
                self.page.listen.clear()
                continue

            # --- 解析响应 ---
            response_data = packet.response.body
            if isinstance(response_data, bytes):
                response_data = json.loads(response_data.decode('utf-8'))
            elif isinstance(response_data, str):
                response_data = json.loads(response_data)

            data = response_data.get('data', {})
            extracted = self._extract_comments_data(response_data)
            all_comments.extend(extracted)
            print(f"📄 本批获取 {len(extracted)} 条评论 | 累计 {len(all_comments)} 条")

            # --- 检查页面底部结束标识 ---
            if self.page.ele('css:div.end-container', timeout=2):
                print("✅ 检测到页面结束标识（- THE END -），所有评论已加载完毕")
                break

            # 未到底，清空已处理的包，滚动到底部继续加载
            self.page.listen.clear()
            scroller.scroll.to_bottom()
            time.sleep(2.5)

        self.page.listen.stop()
        return all_comments