from pathlib import Path
from typing import List

from fastapi import Depends, Query, APIRouter, HTTPException

from backend.business.models.exceptions import NoDataFoundError
from backend.business.models.schemas import FunctionSimilarity, MajorSimilarity, MajorIntroChunk, JobNamesRequest, \
    ProvinceCount, SkillByUidRequest, SkillByUidResponse, VectorMatchRequest, VectorMatchResponse, VectorMatchItem, \
    SimilarityQueryRequest, MajorFunctionSimilarity, ExplanationItem, MatchExplainResponse, MatchExplainRequest, \
    DomainScore, DomainMatchingResponse, DomainMatchingRequest, MatchAggregatedScoreResponse, \
    MatchAggregatedScoreRequest, SkillByUidCountResponse, SkillCountItem, MajorHeatListResponse, MajorHeatItem, \
    SentimentRequest, SentimentResponse
from backend.business.models.api_response import ApiResponse
from backend.business.repository.job_data_repository import JobDataRepository
from backend.business.repository.job_list_repository import JobListRepository
from backend.business.repository.job_location_repository import JobLocationRepository
from backend.business.repository.job_major_repository import JobMajorRepository
from backend.business.repository.major_repository import MajorRepository
from backend.business.repository.sentiment_repository import SentimentRepository
from backend.business.repository.vector_repository import VectorRepository
from backend.business.services.job_data_service import JobSkillService
from backend.business.services.job_list_service import JobListService
from backend.business.services.job_location_service import JobLocationService
from backend.business.services.job_major_service import JobMajorService
from backend.business.services.major_data_service import MajorDataService
from backend.business.services.major_status_service import MajorStatusService
from backend.business.services.match_explain_service import MatchExplainService
from backend.business.services.sentiment_service import SentimentService
from backend.business.services.vector_match_service import VectorMatchService
from backend.business.utils.skill_extractor import SkillExtractor

router = APIRouter(prefix="/achieve", tags=["专业与岗位匹配"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------- 全局单例 ----------

# 1. 轻量文件读取服务（JSON、CSV）
_major_status_service = MajorStatusService(
    _PROJECT_ROOT / 'data' / 'json' / '51job_major_status.json'
)

_major_repo = MajorRepository(
    _PROJECT_ROOT / 'data' / 'db' / 'majors.db'
)

_major_data_service = MajorDataService(
    _PROJECT_ROOT / 'data' / 'csv' / 'major_data.csv',
    _major_repo
)

_skill_extractor = SkillExtractor(
    _PROJECT_ROOT / 'data' / 'json' / 'skills.json'
)

# 2. 向量数据仓库（加载 .npy 文件，通常很大）
_vector_repository = VectorRepository(
    job_npy_path=_PROJECT_ROOT / 'data' / 'npy' / 'job_vectors.npy',
    job_json_path=_PROJECT_ROOT / 'data' / 'npy' / 'job_vectors.json',
    major_npy_path=_PROJECT_ROOT / 'data' / 'npy' / 'major_vectors.npy',
    major_json_path=_PROJECT_ROOT / 'data' / 'npy' / 'major_vectors.json',
)

# 3. 向量匹配服务（依赖 VectorRepository）
_match_service = VectorMatchService(_vector_repository)

# 4. 岗位数据仓库（CSV 可能较大，也缓存之）
_job_data_repo_csv = JobDataRepository(
    _PROJECT_ROOT / 'data' / 'csv' / 'job_data.csv'
)

# 5. 匹配解释服务（加载 ML 模型，非常重量级）
#    注意：这里需要实例化一个 JobDataRepository，我们使用上面的全局单例
_match_explain_service = MatchExplainService(
    major_data_service=_major_data_service,
    job_data_repo=_job_data_repo_csv,
    model_path=_PROJECT_ROOT / 'models' / 'bge_m3' / 'bge-m3',
    lora_path=_PROJECT_ROOT / 'models' / 'bge_m3' / 'bge-m3-latest'
    if (_PROJECT_ROOT / 'models' / 'bge_m3' / 'bge-m3-latest').exists()
    else None
)

def get_sentiment_repository():
    db_path = _PROJECT_ROOT / 'data' / 'db' / 'sentiment_analysis.db'   # 根据实际路径调整
    return SentimentRepository(db_path)

# ---------- 依赖注入 ----------
def get_repository():
    """数据库相关，每次仍可新建（SQLite 连接轻量，可按需改为单例，此处省略）"""
    db_path = _PROJECT_ROOT / 'data' / 'db' / 'job_major_similarity.db'
    return JobMajorRepository(db_path)

def get_service(repo: JobMajorRepository = Depends(get_repository)):
    return JobMajorService(repo)

def get_major_status_service() -> MajorStatusService:
    return _major_status_service

def get_major_data_service() -> MajorDataService:
    return _major_data_service

def get_skill_extractor() -> SkillExtractor:
    return _skill_extractor

# 岗位列表服务（JSON 读取，也可缓存）
# 原 get_job_data_repository 有两个同名的定义，这里合并为一个辅助
def get_job_list_repository() -> JobListRepository:
    json_path = _PROJECT_ROOT / 'data' / 'json' / '51job_job_data.json'
    return JobListRepository(json_path)

def get_job_list_service(repo: JobListRepository = Depends(get_job_list_repository)):
    return JobListService(repo)

def get_job_data_repository() -> JobDataRepository:
    return _job_data_repo_csv

def get_job_skill_service(
    job_list_service: JobListService = Depends(get_job_list_service),
    skill_service: SkillExtractor = Depends(get_skill_extractor),
    csv_repo: JobDataRepository = Depends(get_job_data_repository)
) -> JobSkillService:
    return JobSkillService(job_list_service, skill_service, csv_repo)

def get_job_location_repository():
    db_path = _PROJECT_ROOT / 'data' / 'db' / 'jobs.db'
    return JobLocationRepository(db_path)

def get_service_job_location(repo: JobLocationRepository = Depends(get_job_location_repository)):
    return JobLocationService(repo)

def get_match_service() -> VectorMatchService:
    return _match_service

def get_match_explain_service() -> MatchExplainService:
    return _match_explain_service

def get_sentiment_service(repo: SentimentRepository = Depends(get_sentiment_repository)) -> SentimentService :
    return SentimentService(repo)

# ---------- 路由（Controller）----------
@router.get("/by-major/{major_name}", response_model=ApiResponse[List[FunctionSimilarity]])
def functions_by_major(major_name: str, limit: int = Query(15, ge=1),
                       service: JobMajorService = Depends(get_service)):
    data = service.get_top_functions_for_major(major_name, limit)  # 正常返回数据，异常交给处理器
    return ApiResponse(success=True, data=data, message="OK")

@router.get("/by-function/{function_name}", response_model=ApiResponse[List[MajorSimilarity]])
def majors_by_function(function_name: str, limit: int = Query(15, ge=1),
                       service: JobMajorService = Depends(get_service)):
    print(f"[DEBUG] function_name = {function_name}")
    data = service.get_top_majors_for_function(function_name, limit)
    return ApiResponse(success=True, data=data, message="OK")

@router.get("/get-major", response_model=ApiResponse[dict])
def get_major_status(service: MajorStatusService = Depends(get_major_status_service)):
    data = service.get_all_major_status()
    return ApiResponse(success=True, data=data, message="OK")

@router.get("/get-major-data/{major_name}", response_model=ApiResponse[MajorIntroChunk])
async def get_major_intro_chunks(
    major_name: str,
    service: MajorDataService = Depends(get_major_data_service)
):
    chunks = service.get_intro_chunks_by_major(major_name)
    return ApiResponse(success=True, data=chunks, message="OK")

@router.post("/job-province-counts", response_model=ApiResponse[List[ProvinceCount]])
def job_province_counts(
    request: JobNamesRequest,
    service: JobLocationService = Depends(get_service_job_location)
):
    if not request.job_names:
        raise HTTPException(status_code=400, detail="job_names 不能为空")
    data = service.get_province_counts(request.job_names)
    return ApiResponse(success=True, data=data, message="OK")

@router.get("/get-job-list", response_model=ApiResponse[dict])
def get_job_data(
    service: JobListService = Depends(get_job_list_service)
):
    data = service.get_job_data()
    return ApiResponse(success=True, data=data, message="OK")

@router.post("/job-skills", response_model=ApiResponse[SkillByUidResponse])
def get_job_skills_by_uid(
    req: SkillByUidRequest,
    service: JobSkillService = Depends(get_job_skill_service)
):
    print(f"[DEBUG] req = {req}")
    result = service.get_skills_by_uid(req.uid)

    if "error" in result:
        return ApiResponse(success=False, message=result["error"])

    return ApiResponse(
        success=True,
        data=SkillByUidResponse(**result),
        message="OK"
    )

@router.post("/similarity-between", response_model=ApiResponse[MajorFunctionSimilarity])
def get_similarity_between(
    req: SimilarityQueryRequest,
    service: JobMajorService = Depends(get_service)   # 使用已有的 service 工厂
):
    """
    给定 major_name 和 function_name，返回一对一的匹配分数。
    """
    try:
        result = service.get_similarity_between_major_and_function(
            req.major_name, req.function_name
        )
    except NoDataFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(success=True, data=result, message="OK")

@router.post("/vector-match-major-job", response_model=ApiResponse[VectorMatchResponse])
def match_major_job(
    req: VectorMatchRequest,
    service: VectorMatchService = Depends(get_match_service)
):
    try:
        major_name, job_name, matches = service.compute_job_major_matches(
            req.majorName, req.jobName
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    match_items = [VectorMatchItem(index=idx, similarity=sim) for idx, sim in matches]
    return ApiResponse(
        success=True,
        data=VectorMatchResponse(majorName=major_name, jobName=job_name, matches=match_items),
        message="OK"
    )

@router.post("/explain-matching", response_model=ApiResponse[MatchExplainResponse])
def explain_matching(
    req: MatchExplainRequest,
    service: MatchExplainService = Depends(get_match_explain_service)
):
    try:
        explanations = service.explain_for(
            req.major_name, req.function_name,
            top_k=req.top_k, num_samples=req.num_samples
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    exp_items = [ExplanationItem(**exp) for exp in explanations]
    return ApiResponse(
        success=True,
        data=MatchExplainResponse(
            major_name=req.major_name,
            function_name=req.function_name,
            explanations=exp_items
        ),
        message="OK"
    )

@router.post("/domain-matching", response_model=ApiResponse[DomainMatchingResponse])
def get_domain_matching(
    req: DomainMatchingRequest,
    match_explain_svc: MatchExplainService = Depends(get_match_explain_service),
    skill_extractor: SkillExtractor = Depends(get_skill_extractor),
    job_data_repo: JobDataRepository = Depends(get_job_data_repository)
):
    try:
        domains = match_explain_svc.get_domain_scores(
            major_name=req.majorName,
            function_name=req.functionName,
            skill_extractor=skill_extractor,
            job_data_repo=job_data_repo
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    domain_scores = [DomainScore(**d) for d in domains]
    return ApiResponse(
        success=True,
        data=DomainMatchingResponse(
            major_name=req.majorName,
            function_name=req.functionName,
            domains=domain_scores
        ),
        message="OK"
    )

@router.post("/major-job-aggregated-score", response_model=ApiResponse[MatchAggregatedScoreResponse])
def get_major_job_aggregated_score(
    req: MatchAggregatedScoreRequest,
    match_explain_svc: MatchExplainService = Depends(get_match_explain_service)
):
    try:
        agg = match_explain_svc.score_aggregated_match(
            major_name=req.majorName,
            function_name=req.functionName
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse(
        success=True,
        data=MatchAggregatedScoreResponse(
            major_name=req.majorName,
            function_name=req.functionName,
            max=agg['max'],
            mean=agg['mean'],
            median=agg['median']
        ),
        message="OK"
    )

@router.post("/job-skills-count", response_model=ApiResponse[SkillByUidCountResponse])
def get_job_skills_count(
    req: SkillByUidRequest,          # 复用 uid 请求模型
    service: JobSkillService = Depends(get_job_skill_service)
):
    result = service.get_skills_with_count_by_uid(req.uid)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return ApiResponse(
        success=True,
        data=SkillByUidCountResponse(
            uid=result["uid"],
            function_name=result["function_name"],
            skills=[SkillCountItem(**item) for item in result["skills"]]
        ),
        message="OK"
    )

@router.get("/hot-majors", response_model=ApiResponse[MajorHeatListResponse])
def hot_majors(
    limit: int = Query(30, ge=1, le=100),
    service: MajorDataService = Depends(get_major_data_service)
):
    items = service.get_hot_majors(limit)
    majors = [MajorHeatItem(**item) for item in items]
    return ApiResponse(success=True, data=MajorHeatListResponse(majors=majors), message="OK")

@router.post("/sentiment-analysis", response_model=ApiResponse[SentimentResponse])
def sentiment_analysis(
    req: SentimentRequest,
    service: SentimentService = Depends(get_sentiment_service)
):
    data = service.get_sentiment_analysis(req.major)
    if data is None:
        raise HTTPException(status_code=404, detail=f"专业 {req.major} 的情感数据不存在")
    return ApiResponse(success=True, data=SentimentResponse(**data), message="OK")