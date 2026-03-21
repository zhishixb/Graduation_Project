# backend/websocket_manager.py
from fastapi import WebSocket
from typing import List
import asyncio
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    # ❌ 删除 accept()，只保留添加逻辑
    async def connect(self, websocket: WebSocket):
        # 假设外部已经调用过 accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 连接已注册。当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket 连接已移除。当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
            # 可选：调试成功后再开启，平时太吵
            # logger.debug(f"消息发送成功: {message.get('type')}")
        except Exception as e:
            # 🔴 关键：使用 logger.exception 自动打印堆栈跟踪，而不仅仅是消息
            logger.exception(f"🚫 [WebSocket] 发送消息失败 (连接可能已断开): {e}")
            # 注意：这里依然不 raise，因为这是后台推送，断了就断了，不要崩溃主线程
            # 如果需要断开连接清理资源，可以在这里调用 self.disconnect(websocket)

    def send_message_from_thread(self, message: dict, websocket: WebSocket):
        logger.debug("📩 准备从线程发送消息...")

        if self.loop is None:
            logger.error("💥 事件循环未初始化")
            return

        if websocket not in self.active_connections:
            logger.debug("⚠️ 数据发送失败：目标连接已不存在")
            return

        # 提交任务
        future = asyncio.run_coroutine_threadsafe(
            self.send_personal_message(message, websocket),
            self.loop
        )

        # ✅ 关键修改：使用回调处理结果，而不是阻塞等待 .result()
        def _check_result(fut):
            try:
                # 尝试获取结果，如果协程内抛出了未捕获的异常，这里会收到
                fut.result()
            except Exception as e:
                # 如果 send_personal_message 内部没有捕获异常，会到这里
                logger.exception(f"💥 [后台任务] 消息发送协程崩溃: {e}")
            else:
                # 如果一切正常（包括内部捕获了异常并正常返回），走到这里
                # 不需要打印 None，太吵了
                pass

        future.add_done_callback(_check_result)

        logger.debug("✅ 消息发送任务已提交")


manager = ConnectionManager()