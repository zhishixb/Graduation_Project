from typing import Optional, Dict, Any, Callable
from loguru import logger

# 引入核心组件
from backend.services.spider.platforms.job_51.spider_major import SpiderMajor
from backend.services.spider.platforms.job_51.spider_position import SpiderPosition
from backend.services.spider.platforms.job_51.spider_run import SpiderRunner
from backend.websocket_manager import manager


class SpiderRuntimeController:
    """
    爬虫业务控制器。
    负责：
    1. 根据类型实例化具体的爬虫类。
    2. 包装 WebSocket 回调逻辑。
    3. 管理 SpiderRunner 的生命周期。
    """

    def __init__(self, task_id: str, websocket):
        self.task_id = task_id
        self.websocket = websocket
        self.runner: Optional[SpiderRunner] = None
        self.spider_type: str = ""

        # 用于记录最终状态，防止重复发送完成消息
        self._is_completed = False

    def create_spider(self, spider_type: str, **kwargs) -> bool:
        """
        根据类型创建具体的爬虫实例，并绑定 Runner。
        :param spider_type: 'major' (专业) 或 'position' (职位)
        :param kwargs: 爬虫所需的参数 (如 keyword, city, page_size 等)
        """
        try:
            spider_instance = None

            if spider_type == "major":
                spider_instance = SpiderMajor(**kwargs)
                self.spider_type = "major"
            elif spider_type == "position":
                spider_instance = SpiderPosition(**kwargs)
                self.spider_type = "position"
            else:
                logger.error(f"未知的爬虫类型: {spider_type}")
                return False

            if not spider_instance:
                return False

            # 初始化 Runner
            self.runner = SpiderRunner(spider_instance)
            logger.info(f"[{self.task_id}] 爬虫实例创建成功")
            return True

        except Exception as e:
            logger.exception(f"[{self.task_id}] 创建爬虫实例失败: {e}")
            return False

    def _build_progress_callback(self) -> Callable:
        """
        构建进度回调函数。
        """

        def progress_handler(data: Dict[str, Any]):
            """
            实际执行的回调逻辑。
            data 预期格式: {"job": "...", "page_num": 1, "count": 10, "target": 100}
            """
            # 1. 安全检查
            if self.websocket not in manager.active_connections:
                return

            try:
                # 2. 组装业务数据 (原 payload)
                business_data = {
                    "type": int(data.get("type", 0)),
                    "current_job": str(data.get("current_job", "")),
                    "current_page": int(data.get("current_page", 0)),
                    "current_count": int(data.get("current_count", 0)),
                    "target_count": int(data.get("target_count", 0)),
                }

                # 3. 组装标准响应结构
                # 成功状态：success=True, message="progress_update", data=业务数据
                response_payload = {
                    "success": True,
                    "message": "progress_update",  # 可选：给前端一个明确的操作标识
                    "data": business_data
                }

                # 4. 线程安全发送
                if hasattr(manager, 'send_message_from_thread'):
                    # 发送整个标准结构的字典
                    logger.debug("准备向前端报告进度")
                    manager.send_message_from_thread(response_payload, self.websocket)
                else:
                    logger.error("Manager 缺少线程安全发送方法")

            except Exception as e:
                logger.error(f"[{self.task_id}] 构建或发送进度消息失败: {e}")

        return progress_handler


    def start(self, **kwargs) -> bool:
        """
        启动爬虫任务。
        """
        if not self.runner:
            logger.error(f"[{self.task_id}] 请先调用 create_spider 初始化。")
            return False

        if self.runner.is_running():
            logger.warning(f"[{self.task_id}] 任务已在运行中。")
            return False

        progress_cb = self._build_progress_callback()

        # 启动 Runner (这只是启动了线程，瞬间返回)
        success = self.runner.start(progress_callback=progress_cb)

        if not success:
            return False

        logger.info(f"[{self.task_id}] 爬虫线程已启动，现在阻塞等待其结束...")

        try:
            if self.runner._thread:
                self.runner._thread.join()
        except Exception as e:
            logger.error(f"[{self.task_id}] 等待线程结束时出错: {e}")

        logger.info(f"[{self.task_id}] 爬虫线程已彻底结束。")
        return True

    def stop(self, timeout: float = 5.0) -> bool:
        """
        停止爬虫任务。
        """
        if not self.runner:
            return False
        return self.runner.stop(timeout=timeout)

    def is_running(self) -> bool:
        if not self.runner:
            return False
        return self.runner.is_running()