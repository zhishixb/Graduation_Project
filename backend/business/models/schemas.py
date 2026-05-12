from typing import List, Tuple, Optional

from pydantic import BaseModel, Field, ConfigDict

class FunctionSimilarity(BaseModel):
    function_name: str
    similarity: float

class MajorSimilarity(BaseModel):
    major_name: str
    similarity: float


class MajorFunctionSimilarity(BaseModel):
    major_name: str
    function_name: str
    similarity: float

class SimilarityQueryRequest(BaseModel):
    major_name: str = Field(alias="majorName")
    function_name: str = Field(alias="functionName")

    model_config = ConfigDict(populate_by_name=True)


class MajorIntroChunk(BaseModel):
    """专业介绍分块信息"""
    main_courses: str = ""
    training_direction: str = ""
    description: str = ""
    employment_direction: str = ""


class JobNamesRequest(BaseModel):
    job_names: List[str]

class ProvinceCount(BaseModel):
    name: str
    value: int


class SkillByUidRequest(BaseModel):
    uid: int

class SkillByUidResponse(BaseModel):
    uid: int
    function_name: str
    skills: List[str]
    category: List[str]


class VectorMatchRequest(BaseModel):
    majorName: str
    jobName: str

class VectorMatchItem(BaseModel):
    index: int           # 在 job_embeddings 中的原始行索引
    similarity: float

class VectorMatchResponse(BaseModel):
    majorName: str
    jobName: str
    matches: List[VectorMatchItem]


# 请求模型
class MatchExplainRequest(BaseModel):
    major_name: str
    function_name: str
    top_k: int = 5           # 解释结果中保留的词法/语义对数量
    num_samples: int = 5     # 随机抽取的岗位文本数

# 单条解释结果
class ExplanationItem(BaseModel):
    job_text: str
    lexical_contrib: List[Tuple[str, float]]
    semantic_pairs: List[Tuple[str, str, float]]
    echarts_json: Optional[str] = None

# 整体响应
class MatchExplainResponse(BaseModel):
    major_name: str
    function_name: str
    explanations: List[ExplanationItem]


class DomainScore(BaseModel):
    category: str
    score: float

class DomainMatchingRequest(BaseModel):
    majorName: str = Field(alias="majorName")
    functionName: str = Field(alias="functionName")

class DomainMatchingResponse(BaseModel):
    major_name: str
    function_name: str
    domains: List[DomainScore]


class MatchAggregatedScoreResponse(BaseModel):
    major_name: str
    function_name: str
    max: float
    mean: float
    median: float

class MatchAggregatedScoreRequest(BaseModel):
    majorName: str
    functionName: str