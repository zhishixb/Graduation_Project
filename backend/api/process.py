from fastapi import APIRouter, HTTPException, status
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.controllers.clean_data_controller import CleanDataController

router = APIRouter(prefix="/api/process", tags=["数据处理"])

# 创建一个线程池，用于运行耗时的同步任务
# max_workers 可根据 CPU 核心数调整，默认通常足够
executor = ThreadPoolExecutor(max_workers=5)

@router.get("/checkMajorStatus")
async def check_major_status():
    controller = CleanDataController()
    res = controller.is_majors_cleand()
    return res


@router.get("/cleanMajor")
async def clean_majors():
    """
    【HTTP GET】触发专业数据清洗任务
    注意：这是一个耗时操作，已放入线程池执行以避免阻塞主线程。
    """
    logger.info("📥 收到清洗请求，开始执行...")

    try:
        # 1. 定义同步执行函数
        def run_cleaning():
            controller = CleanDataController()
            return controller.clean_major_data()

        # 2. 在线程池中运行同步任务 (非阻塞)
        # 这样不会卡住 FastAPI 的主事件循环
        result = await asyncio.get_event_loop().run_in_executor(executor, run_cleaning)

        # 3. 处理返回结果
        if result.get("success"):
            logger.success(f"✅ 清洗任务成功完成：{result.get('message')}")
            return result
        else:
            # 业务逻辑失败 (如文件不存在、处理中断)
            logger.error(f"❌ 清洗任务业务失败：{result.get('message')}")
            # 根据错误类型决定状态码，这里统一用 500 或 400
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "未知业务错误")
            )

    except HTTPException:
        # 重新抛出 HTTPException，避免被下面的 except 捕获变成 500
        raise
    except Exception as e:
        # 捕获系统级未预期异常 (如内存溢出等)
        logger.critical(f"💥 清洗任务发生系统级崩溃：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"系统内部错误：{str(e)}"
        )