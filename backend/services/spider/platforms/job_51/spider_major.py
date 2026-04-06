import time
from pathlib import Path
from loguru import logger
from sklearn.utils.multiclass import type_of_target

from backend.services.spider.platforms.job_51.private.major_spider.dao import JobDatabaseManager
from backend.services.spider.platforms.job_51.private.major_spider.get_target_tools import get_geometric_probabilities
from backend.services.spider.platforms.job_51.private.major_spider.job_data_parser import JobDataParser
from backend.services.spider.platforms.job_51.private.major_spider.major_dictionary import MajorDictionary
from backend.services.spider.platforms.job_51.private.major_spider.major_status_manager import MajorStatusManager
from backend.services.spider.platforms.job_51.private.major_spider.url_manager import SpiderUrlManager
from backend.services.spider.platforms.job_51.public.browser_manager import BrowserSessionManager
from backend.services.spider.platforms.job_51.public.spider_run_signal import SpiderRunSignal

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_DEFAULT_FILE_PATH_BASE = _PROJECT_ROOT / 'data' / 'json' / '51job_major_data.json'
_DEFAULT_DB_PATH_BASE = _PROJECT_ROOT / 'data' / 'db' / 'job_data.db'


class SpiderMajor:
    def __init__(self, subject: str,  secondary_subject: str, major: str):
        """
        初始化爬虫实例。

        每个实例都应该是独立的，可以在一个线程中运行。
        """
        self.subject = subject
        self.secondary_subject = secondary_subject
        self.major = major
        self.file_path = _DEFAULT_FILE_PATH_BASE
        self.db_path = _DEFAULT_DB_PATH_BASE

        # --- 每个实例都拥有自己独立的工具 ---
        self.major_status = MajorStatusManager(self.file_path, self.subject, self.secondary_subject, self.major)
        self.browser_session = BrowserSessionManager()
        self.job_data_parser = JobDataParser()
        self.job_database_manager = JobDatabaseManager(self.db_path, self.major)
        self.major_state_store = MajorDictionary()
        self.url_manager = None

        # 用于标识爬虫是否正在运行
        self._is_running = False
        # 终止爬虫标志
        self._stop_requested = False

        # 创建一个实例专属的 logger，预设 extra 信息
        # 这样就不需要在每次调用 logger.info 时都写 extra
        self.logger = logger.bind(spider_name=self.subject, major=self.major)

    def run(self, progress_callback=None):
        """
        启动爬虫主流程。这个方法是线程安全的入口点。
        """
        if self._is_running:
            # 注意：现在使用 self.logger，它已经绑定了 extra 信息
            self.logger.info(f"[{self.major}] 爬虫已在运行中，忽略重复启动请求。")
            return

        job = "未开始"
        page_num = 0
        count = 0
        target = 0

        self._is_running = True
        self._stop_requested = False
        # 使用 self.logger 替代全局 logger
        self.logger.info(f"[{self.major}] 爬虫启动...")

        try:
            # 1. 检查是否已完成
            if self.major_status.are_all_jobs_completed():
                self.logger.info(f"[{self.major}] 所有任务已完成，爬虫退出。")
                return

            # 2. 初始化目标计数
            summary = self.major_status.get_progress_summary()
            if summary['total_target'] == 0:
                jobs = self.major_status.get_all_job_names()
                self.logger.info(f"获取到的岗位: {jobs}")
                jobs_data = get_geometric_probabilities(jobs)
                self.major_status.update_target_counts(jobs_data)

            # 3. 开始爬取循环

            # 使用 with 语句管理浏览器会话
            with self.browser_session as session:
                while not self.major_status.are_all_jobs_completed() and not self._stop_requested:
                    job_mes = self.major_status.get_next_pending_job()
                    if not job_mes:
                        break

                    # ✅ 修复：使用 self.logger 而不是 self.logger
                    self.logger.info(f"开始处理: {job_mes}")

                    page_num = 1

                    job = job_mes[0]
                    self.url_manager = SpiderUrlManager(job)

                    target = job_mes[1]
                    count = job_mes[2]

                    while count < target and not self._stop_requested:
                        if progress_callback:
                            signal_obj = SpiderRunSignal(
                                type = 1,
                                current_job=job,
                                current_page=page_num,
                                current_count=count,
                                target_count=target,
                            )
                            progress_callback(signal_obj.to_dict())

                        target_url = self.url_manager.get_url(page_num)
                        result = session.solve_and_get_data(target_url, max_retries=3)

                        if result['success']:
                            data = result['data']
                            parse_success, parsed_list, parse_message = self.job_data_parser.parse_listings(data)

                            if parse_success and parsed_list:
                                length = len(parsed_list)
                                if self.job_database_manager.insert_parsed_data(parsed_list):
                                    # ✅ 修复：使用 self.logger
                                    self.logger.success(f"第 {page_num} 页爬取成功")
                                    page_num += 1
                                    count += length
                                    self.major_status.update_fetched_count(job, length)

                                else:
                                    # ✅ 修复：使用 self.logger
                                    self.logger.error(f"❌ 数据库插入失败: {parse_message}")
                            else:
                                if parse_success and not parsed_list:
                                    page_num = 1
                                    # 切换时间戳查询，应该有效
                                    self.url_manager = SpiderUrlManager(job)
                                else:
                                    self.logger.error(f"❌ 解析失败: {parse_message}")
                        else:
                            # ✅ 修复：使用 self.logger
                            self.logger.warning("获取失败，请检查日志或网络环境。")

                        time.sleep(3)

                    if count >= target:
                        self.major_status.mark_job_as_completed(job)

                if self.major_status.are_all_jobs_completed():
                    self.major_state_store.set_major_state(self.subject, self.secondary_subject, self.major)

        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止...")
        finally:
            self._is_running = False
            self.logger.info("爬虫任务结束。")
            if progress_callback:
                signal_obj = SpiderRunSignal(
                    type=2,
                    current_job=job or "",
                    current_page=page_num,
                    current_count=count,
                    target_count=target,
                )
                progress_callback(signal_obj.to_dict())

    def to_stop(self):
        """
        请求停止爬虫。这是一个非阻塞的请求，爬虫将在下一个检查点安全退出。
        """
        self.logger.info(f"[{self.major}] 接收到外部停止请求。")
        self._stop_requested = True

    def is_running(self):
        """
        查询爬虫是否正在运行。
        """
        return self._is_running