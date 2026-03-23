from fastapi import APIRouter, HTTPException
from backend.controllers.job_dict_controller import JobDictController, TrainingDataCountController

router = APIRouter(prefix="/api/spider", tags=["爬虫功能"])


@router.get("/allMajors")
async def get_all_jobs():
    """
    【HTTP GET】获取所有职位层级数据
    前端调用示例: GET /api/job-dict/all
    """
    # 1. 实例化 Controller (无状态，用完即弃)
    controller = JobDictController()

    # 2. 调用业务逻辑
    result = controller.get_full_major_dictionary()

    # 3. 处理返回
    if result["success"]:
        return result
    else:
        # 如果控制器返回失败，抛出 HTTP 500 或 400
        raise HTTPException(status_code=500, detail=result["message"])

@router.get("/allJobs")
async def get_all_jobs():
    """
    【HTTP GET】获取所有职位层级数据
    前端调用示例: GET /api/job-dict/all
    """
    # 1. 实例化 Controller (无状态，用完即弃)
    controller = JobDictController()

    # 2. 调用业务逻辑
    result = controller.get_full_job_dictionary()

    # 3. 处理返回
    if result["success"]:
        return result
    else:
        # 如果控制器返回失败，抛出 HTTP 500 或 400
        raise HTTPException(status_code=500, detail=result["message"])

@router.get("/getTrainingDataCount")
async def get_training_data_count():
    training_data_count = TrainingDataCountController()
    return training_data_count.get_training_data_count()