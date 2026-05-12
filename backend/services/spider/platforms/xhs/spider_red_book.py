from pathlib import Path
import time
from loguru import logger

from backend.services.spider.platforms.job_51.public.spider_run_signal import SpiderRunSignal
from backend.services.spider.platforms.xhs.comment_parser import CommentParser
from backend.services.spider.platforms.xhs.dao import CommentDataManager
from backend.services.spider.platforms.xhs.majors_processor import MajorsProcessor
from backend.services.spider.platforms.xhs.spider_core import XHSSpiderCore
from backend.services.spider.platforms.xhs.url_manager import UrlManager


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_DEFAULT_COMMENTS_DB_PATH_BASE = _PROJECT_ROOT / 'data' / 'db' / 'comments.db'
_DEFAULT_MAJOR_DB_PATH_BASE = _PROJECT_ROOT / 'data' / 'db' / 'majors.db'
_DEFAULT_USER_DATA_PATH_BASE = Path(__file__).resolve().parent / 'user_data'


class SpiderRedBook:
    def __init__(self, major: str):
        self.major = major
        self.url_manager = UrlManager(major)
        self.database_manager = CommentDataManager(_DEFAULT_COMMENTS_DB_PATH_BASE)
        self.majors_processor = MajorsProcessor(_DEFAULT_MAJOR_DB_PATH_BASE)
        self.comments_parser = CommentParser()
        self.spider_core = XHSSpiderCore(
            user_data_dir=_DEFAULT_USER_DATA_PATH_BASE,
            target_note_count=20,
            search_scroll_times=6,
            comment_max_scroll=50
        )

        self.logger = logger.bind(major=self.major)

        self._is_running = False
        self._stop_requested = False

    def to_stop(self):
        """请求停止爬虫（优雅退出）"""
        self._stop_requested = True
        self.logger.info(f"[{self.major}] 收到停止请求")

    def run(self, progress_callback=None):
        if self._is_running:
            self.logger.warning(f"[{self.major}] 爬虫已在运行中，忽略重复启动请求。")
            return

        self._is_running = True
        self._stop_requested = False

        count = 1
        start_type = 0
        length = 0

        try:
            # 1. 获取专业处理状态
            major_status = self.majors_processor.get_first_unprocessed()
            if major_status is None:
                self.logger.info(f"[{self.major}] 没有待处理专业（可能全部已完成）")
                return

            if major_status['is_processed'] == 1:
                self.logger.info(f"[{self.major}] 专业已完成处理，无需重复执行")
                return

            start_type = 0
            if major_status['is_processed'] == 0:
                start_type = 1
            self.logger.info(f"[{self.major}] 开始处理，起始轮次 type={start_type}")

            stock = self.database_manager.count_by_major(self.major)

            if stock > 1000 and start_type == 0:
                start_type = 1
            elif stock > 2000 and start_type == 1:
                self.majors_processor.mark_processed_by_name(self.major, start_type)
                return

            for round_type in range(start_type, 2):
                if progress_callback:
                    signal_obj = SpiderRunSignal(
                        type=0, # 开始类型
                        current_job=self.major + "正在获取列表",
                        current_page=start_type,
                        current_count=0,
                        target_count=1,
                    )
                    progress_callback(signal_obj.to_dict())

                if self._stop_requested:
                    self.logger.info(f"[{self.major}] 收到停止信号，中止采集")
                    break

                count = 0

                # 2. 构造搜索 URL
                search_url = self.url_manager.get_url(round_type)
                self.logger.info(f"[{self.major}] 第 {round_type} 轮搜索 URL: {search_url[:100]}...")

                # 3. 获取笔记列表
                try:
                    note_list = self.spider_core.search_notes(search_url)
                except Exception as e:
                    self.logger.error(f"[{self.major}] 搜索笔记失败: {e}")
                    continue

                if not note_list:
                    self.logger.warning(f"[{self.major}] 第 {round_type} 轮未获取到任何笔记")
                    # 即使没有笔记也标记该轮完成（避免死循环）
                    # self.majors_processor.mark_processed_by_name(self.major, start_type)
                    continue

                length = len(note_list)

                # 4. 遍历笔记采集评论
                for idx, note in enumerate(note_list, 1):
                    if self._stop_requested:
                        break

                    if stock > 2000 and start_type == 0:
                        start_type = 1
                    elif stock > 4000 and start_type == 1:
                        self.majors_processor.mark_processed_by_name(self.major, start_type)
                        return

                    if progress_callback:
                        signal_obj = SpiderRunSignal(
                            type=1,
                            current_job=self.major,
                            current_page=start_type,
                            current_count=count,
                            target_count=length,
                        )
                        progress_callback(signal_obj.to_dict())

                    note_id = note['id']
                    # 检查是否已采集过该笔记（避免重复）
                    if self.database_manager.note_exists(note_id):
                        self.logger.debug(f"[{self.major}] 笔记 {note_id} 已存在，跳过")
                        count += 1
                        continue

                    note_url = self.url_manager.get_note_url(note_id, note['xsec_token'])
                    try:
                        comments_raw = self.spider_core.crawl_comments(note_url, max_comments=10000)
                    except Exception as e:
                        self.logger.error(f"[{self.major}] 采集笔记评论失败 {note_url}: {e}")
                        continue

                    if not comments_raw:
                        self.majors_processor.mark_processed_by_name(self.major, start_type)
                        self.logger.info(f"进入无评论帖子，退出爬虫")
                        return

                    # 解析并入库
                    flat_comments = self.comments_parser.parse(comments_raw, note_id)
                    inserted = self.database_manager.save_comments(flat_comments, self.major)
                    self.logger.info(f"[{self.major}] 笔记 {note_id} 入库 {inserted} 条评论")

                    stock += inserted

                    count+=1

                    time.sleep(60)

                # 5. 标记本轮完成
                if count >= 20:
                    self.majors_processor.mark_processed_by_name(self.major, start_type)
                self.logger.success(f"[{self.major}] 第 {round_type} 轮处理完成")

            # 全部完成
            if not self._stop_requested:
                self.logger.success(f"[{self.major}] 所有轮次处理完毕")

        except Exception as e:
            self.logger.exception(f"[{self.major}] 运行过程中发生未捕获异常: {e}")

        finally:
            if progress_callback:
                signal_obj = SpiderRunSignal(
                    type=2,
                    current_job=self.major,
                    current_page=start_type,
                    current_count=count,
                    target_count=length,
                )
                progress_callback(signal_obj.to_dict())
            # 确保资源释放
            # self.logger.info(f"[{self.major}] 正在关闭浏览器...")
            try:
                self.spider_core.quit()
            except Exception as e:
                self.logger.error(f"[{self.major}] 关闭浏览器时出错: {e}")

            try:
                self.database_manager.close()
            except Exception as e:
                self.logger.error(f"[{self.major}] 关闭数据库连接时出错: {e}")

            self._is_running = False
            self.logger.info(f"[{self.major}] 爬虫已停止")