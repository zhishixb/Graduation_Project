import time
from pathlib import Path
from loguru import logger

from backend.services.spider.platforms.job_51.private.position_spider.dao import JobDatabaseManager
from backend.services.spider.platforms.job_51.private.position_spider.job_data_parser import JobDataParser
from backend.services.spider.platforms.job_51.private.position_spider.job_status_manager import JobStatusManager
from backend.services.spider.platforms.job_51.private.position_spider.url_manager import SpiderUrlManager
from backend.services.spider.platforms.job_51.public.browser_manager import BrowserSessionManager
from backend.services.spider.platforms.job_51.public.spider_run_signal import SpiderRunSignal

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_DEFAULT_FILE_PATH_BASE = _PROJECT_ROOT / 'data' / 'json' / '51job_job_data.json'
_DEFAULT_DB_PATH_BASE = _PROJECT_ROOT / 'data' / 'db' / 'jobs.db'

class SpiderPosition:
    def __init__(self, subject: str, secondary_subject: str, major: str):
        self.category = subject
        self.sub_category = secondary_subject
        self.position = major
        self.file_path = _DEFAULT_FILE_PATH_BASE
        self.db_path = _DEFAULT_DB_PATH_BASE

        self.browser_session = BrowserSessionManager()
        self.job_data_parser = JobDataParser()
        self.job_database_manager = JobDatabaseManager(db_path=self.db_path, default_function=self.position)
        self.job_status = JobStatusManager(self.file_path, self.category, self.sub_category, self.position)
        self.url_manager = None

        # 用于标识爬虫是否正在运行
        self._is_running = False
        # 终止爬虫标志
        self._stop_requested = False

        self.logger = logger.bind(spider_name=self.category, major=self.position)

    def run(self, progress_callback=None):
        """
        启动爬虫主流程。这个方法是线程安全的入口点。
        """
        if self._is_running:
            # 注意：现在使用 self.logger，它已经绑定了 extra 信息
            self.logger.info(f"[{self.position}] 爬虫已在运行中，忽略重复启动请求。")
            return

        self._is_running = True
        self._stop_requested = False
        # 使用 self.logger 替代全局 logger
        self.logger.info(f"[{self.position}] 爬虫启动...")

        try:
            # 1. 检查是否已完成
            if not self.job_status.is_pending():
                self.logger.info(f"[{self.position}] 所有任务已完成，爬虫退出。")
                page_num = 1
                count = 150
                print(1111)
                return

            # 3. 开始爬取循环

            # 使用 with 语句管理浏览器会话
            with self.browser_session as session:
                # ✅ 修复：使用 self.logger 而不是 self.logger
                self.logger.info(f"开始处理: {self.position}")

                page_num = 1

                function = self.job_status.get_id()
                self.url_manager = SpiderUrlManager(function)

                print(self.url_manager.get_url(page_num))

                count = self.job_status.get_count()

                while count < 150 and not self._stop_requested:
                    if progress_callback:
                        signal_obj = SpiderRunSignal(
                            type = 1,
                            current_job=self.position,
                            current_page=page_num,
                            current_count=count,
                            target_count=150,
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
                                self.job_status.update_count(count)

                            else:
                                # ✅ 修复：使用 self.logger
                                self.logger.error(f"❌ 数据库插入失败: {parse_message}")
                        else:
                            if parse_success and not parsed_list:
                                page_num = 1
                                self.url_manager = SpiderUrlManager(function)
                            else:
                                self.logger.error(f"❌ 解析失败: {parse_message}")
                    else:
                        # ✅ 修复：使用 self.logger
                        self.logger.warning("本岗位数据已全部爬取。")
                        self.job_status.set_state_completed()

                    time.sleep(3)

                    if count >= 120:
                        self.job_status.set_state_completed()

        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止...")
        finally:
            self._is_running = False
            self.logger.info("爬虫任务结束。")
            if progress_callback:
                signal_obj = SpiderRunSignal(
                    type=2,
                    current_job=self.position,
                    current_page=page_num,
                    current_count=count,
                    target_count=150,
                )
                progress_callback(signal_obj.to_dict())


    def to_stop(self):
        """
        请求停止爬虫。这是一个非阻塞的请求，爬虫将在下一个检查点安全退出。
        """
        self.logger.info(f"[{self.position}] 接收到外部停止请求。")
        self._stop_requested = True

    def is_running(self):
        """
        查询爬虫是否正在运行。
        """
        return self._is_running