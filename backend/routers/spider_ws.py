# backend/api/spider.py
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.controllers.spider_runtime_controller import SpiderRuntimeController
from backend.websocket_manager import manager
from loguru import logger
import concurrent.futures

router = APIRouter()


@router.websocket("/ws/task/{task_id}")
async def websocket_task_endpoint(websocket: WebSocket, task_id: str):
    origin = websocket.headers.get("origin")
    logger.info(f"🔍 [WS] 收到连接请求: TaskID={task_id}, Origin={origin}")

    # 状态标记
    spider_task = None
    is_running = False

    try:
        await websocket.accept()
        await manager.connect(websocket)
        logger.info(f"✅ 连接建立: {task_id}")

        controller = SpiderRuntimeController(task_id=task_id, websocket=websocket)

        # --- 核心逻辑：单一的监听循环 ---
        async def command_listener():
            nonlocal spider_task, is_running

            while True:
                try:
                    # ⚠️ 全局唯一接收点：确保没有任何其他代码调用 receive_json
                    data = await websocket.receive_json()
                    action = data.get("action")
                    logger.info(f"📩 收到指令: {action}")

                    if action == "start":
                        if is_running:
                            logger.warning(f"⚠️ 爬虫已在运行，忽略重复启动请求")
                            await websocket.send_json({"success": False, "message": "Spider already running"})
                            continue

                        spider_type = data.get("type")
                        spider_params = {k: v for k, v in data.items() if k not in ["action", "type"]}

                        logger.info(f"正在创建爬虫: type={spider_type}")
                        if controller.create_spider(spider_type=spider_type, **spider_params):
                            logger.info("✅ 爬虫创建成功，启动后台任务...")
                            is_running = True

                            # 启动独立的后台任务运行爬虫
                            spider_task = asyncio.create_task(run_spider_in_thread(controller))
                        else:
                            logger.error("❌ 创建爬虫失败")
                            await websocket.send_json({"success": False, "message": "Failed to create spider"})

                    elif action == "stop":
                        logger.info(f"🛑 【成功捕获】接收到停止指令！")
                        if not is_running:
                            logger.warning("当前没有运行的爬虫，忽略停止指令")
                        else:
                            controller.stop()
                            await websocket.send_json({"success": True, "message": "Stop signal sent"})
                            # 注意：这里不要直接 break 或 close，除非业务要求停止即断开
                            # 让爬虫任务自己跑完，或者等待任务结束

                    elif action == "ping":
                        await websocket.send_json({"type": "pong"})

                except WebSocketDisconnect:
                    logger.info(f"🔌 客户端主动断开连接")
                    raise  # 抛出异常以便 finally 块处理
                except Exception as e:
                    logger.error(f"❌ 接收消息出错: {e}")
                    raise

        # --- 后台运行爬虫的辅助函数 ---
        async def run_spider_in_thread(ctrl: SpiderRuntimeController):
            try:
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    # 将阻塞的 start() 放入线程池
                    await loop.run_in_executor(pool, ctrl.start)
            except Exception as e:
                logger.error(f"❌ 爬虫运行异常: {e}")
                try:
                    await websocket.send_json({"success": False, "message": f"Spider crashed: {str(e)}"})
                except:
                    pass
            finally:
                nonlocal is_running
                is_running = False
                logger.info(f"🏁 爬虫任务已结束 (正常或异常)")

        # 启动监听器 (这将一直运行直到连接断开)
        await command_listener()

    except WebSocketDisconnect:
        # 正常断开流程
        pass
    except Exception as e:
        logger.error(f"❌ WS 顶层异常: {type(e).__name__} - {e}")
    finally:
        # --- 清理工作 ---
        logger.info(f"🧹 开始清理资源: {task_id}")

        # 1. 如果爬虫还在跑，强制停止
        if is_running:
            logger.warning("⚠️ 连接关闭时爬虫仍在运行，执行强制停止...")
            controller.stop()
            # 可以选择等待一下线程结束，但不要死等
            # if spider_task: await asyncio.wait_for(spider_task, timeout=2.0)

        # 2. 断开管理器连接
        if websocket in manager.active_connections:
            manager.disconnect(websocket)

        logger.info(f"✨ 清理完成: {task_id}")