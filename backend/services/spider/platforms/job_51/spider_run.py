# backend/services/spider/platforms/job_51/spider_runner.py

import threading
import time
from typing import Optional, Callable, Any, Dict, Union
from loguru import logger

SpiderType = Any


class SpiderRunner:
    """
    通用的爬虫线程管理器。
    支持任何具有 run(), to_stop() 方法的爬虫类。
    """

    def __init__(self, spider: SpiderType):
        self.spider = spider
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._start_time: Optional[float] = None

        # 动态获取标识名称，用于日志
        self._identifier = getattr(spider, 'major', getattr(spider, 'target_name', 'Unknown'))

    def start(self, progress_callback: Optional[Callable] = None) -> bool:
        """
        启动线程。
        不再关心 websocket, task_id, 数据格式。
        只负责在合适的时候调用传入的回调函数。
        """

        # 提供安全的默认空回调，防止外部没传导致报错
        def _noop_progress(*args, **kwargs): pass

        safe_progress = progress_callback or _noop_progress

        with self._lock:
            if self._thread and self._thread.is_alive():
                return False

            # 直接把外界的回调传进去，不做任何包装！
            self._thread = threading.Thread(
                target=self._run_wrapper,
                args=(safe_progress,),
                name=f"Spider-{self._identifier}",
                daemon=False
            )
            self._thread.start()
            self._start_time = time.time()
            return True

    def _run_wrapper(self, callback: Optional[Callable]):
        try:
            # 核心：直接调用 .run()，不管它是哪个类的实例
            self.spider.run(progress_callback=callback)
        except Exception as e:
            logger.exception(f"[{self._identifier}] 发生严重异常: {e}")
        finally:
            logger.debug(f"[{self._identifier}] 线程执行完毕。")

    def stop(self, timeout: float = 5.0) -> bool:
        with self._lock:
            if not self._thread or not self._thread.is_alive():
                logger.warning(f"[{self._identifier}] 任务未运行。")
                return False

            logger.info(f"[{self._identifier}] 请求停止...")
            # 核心：直接调用 .to_stop()
            self.spider.to_stop()

            self._thread.join(timeout=timeout)

            if self._thread.is_alive():
                logger.warning(f"[{self._identifier}] 超时未停止。")
                return False

            logger.info(f"[{self._identifier}] 已安全停止。")
            self._thread = None
            return True

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()