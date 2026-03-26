from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.controllers.models_instruct_controller import ModelsInstructorController

router = APIRouter(prefix="/models", tags=["模型微调"])


# 1. 定义请求体数据模型 (Pydantic Model)
class ModelCompareRequest(BaseModel):
    model_a: str = Field(..., description="第一个模型的逻辑名称 (Key)", example="qwen-base-7b")
    model_b: str = Field(..., description="第二个模型的逻辑名称 (Key)", example="qwen-lora-7b-v1")
    major: str = Field(..., description="要对比的专业名称", example="计算机科学与技术")
    jobs: List[str] = Field(..., description="岗位名称列表", example=["Java开发工程师", "Python后端开发", "产品经理"])


@router.get("/getModelList")
async def get_model_list():
    """获取可用模型列表"""
    controller = ModelsInstructorController()
    data = controller.get_models_list()
    return {
        "success": True,
        "data": data,
        "message": "获取成功"
    }


@router.post("/modelCompare", summary="双模型匹配度对比")
async def compare_models(request: ModelCompareRequest):
    """
    计算指定专业与多个岗位在两个不同模型下的匹配度得分。

    - 使用 POST 方法以支持长列表和复杂数据。
    - 数据通过 JSON Body 传递。
    """
    try:
        controller = ModelsInstructorController()

        # 调用控制器方法
        # 直接从 request 对象中取值，类型安全且清晰
        res = controller.get_model_comparsion(
            model_key_a=request.model_a,
            model_key_b=request.model_b,
            major_name=request.major,
            jobs=request.jobs
        )

        return {
            "success": True,
            "data": res,
            "message": "对比完成"
        }

    except ValueError as e:
        # 处理模型不存在、参数校验失败等逻辑错误 (400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except FileNotFoundError as e:
        # 处理模型文件缺失 (500)
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"模型文件缺失: {str(e)}")

    except Exception as e:
        # 处理其他未知错误 (500)
        # 建议在这里记录详细日志 (logger.error(...))
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"内部服务错误: {str(e)}")