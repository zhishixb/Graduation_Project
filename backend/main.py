import asyncio
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.responses import JSONResponse

from backend.api import spider, process
from backend.business.models.exceptions import BusinessError
from backend.routers import spider_ws
from backend.websocket_manager import manager

from backend.business.controller import api_controller

# 日志
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function} | {message}"

logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level="INFO",
    colorize=True
)

PROJECT_ROOT = Path(__file__).resolve().parent
LOG_PATH = PROJECT_ROOT / "data" / "logs"
LOG_PATH.mkdir(parents=True, exist_ok=True)

logger.add(
    LOG_PATH / "app_{time:YYYYMMDD}.log",
    format=LOG_FORMAT,
    rotation="1 day",
    retention="7 days",
    encoding="utf-8",
    level="INFO",
    colorize=True
)

# fastapi基础配置
app = FastAPI()

# --- 配置 CORS (跨域资源共享) ---
origins = [
    "http://localhost",
    "http://localhost:5173",      # Vite 开发环境默认端口
    "http://127.0.0.1:5173",
    "http://localhost:3000",      # 如果你用 Create React App
    # 生产环境打包后，如果是 file:// 协议或者同端口部署，可能不需要，但加上也没坏处
]

@app.on_event("startup")
async def startup_event():
    # 获取当前运行的事件循环并传递给 manager
    loop = asyncio.get_running_loop()
    manager.set_event_loop(loop)
    # logger.info("FastAPI 启动，WebSocket 管理器已绑定事件循环。")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 允许跨域的源列表
    allow_credentials=True,       # 允许携带 Cookie/认证信息
    allow_methods=["*"],          # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE, OPTIONS...)
    allow_headers=["*"],          # 允许所有 HTTP 头
)

# 注册异常处理
@app.exception_handler(BusinessError)
async def business_exception_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "data": None,
            "message": exc.message
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": f"服务器内部错误：{str(exc)}"
        }
    )

# 自用保留api（按照service、controller层的结构设置）
app.include_router(spider.router)
app.include_router(process.router)
# app.include_router(models_instruct.router)
app.include_router(spider_ws.router)

# 业务api（最终展示界面的api，存在实体类的相关设置，设置为模型类、数据持久层、业务逻辑层、控制器层）
app.include_router(api_controller.router)

if __name__ == "__main__":
    import uvicorn

    # 启动服务器
    uvicorn.run(app, host="127.0.0.1", port=8090)