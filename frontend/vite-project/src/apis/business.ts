import request from '@/utils/request'


export const getMajorStatus = () => {
  return request.get('/achieve/get-major')
}

/**
 * 返回岗位名列表
 * @returns {Promise}
 */
export const getJobList = () => {
  return request.get('/achieve/get-job-list')
}

export const getMajorsByFunction = (functionName: string, limit = 15) => {
  console.log(functionName)
  return request.get(`/achieve/by-function/${encodeURIComponent(functionName)}`, {
    params: { limit }
  })
}

export const getFunctionsByMajor = (majorName: string, limit = 15) => {
  return request.get(`/achieve/by-major/${encodeURIComponent(majorName)}`, {
    params: { limit }
  })
}

export const getMajorData = (majorName: string) => {
  return request.get(`/achieve/get-major-data/${encodeURIComponent(majorName)}`)
}

/**
 * 查询指定岗位名称列表的各省份岗位数量
 * @param {string[]} jobNames - 岗位名称列表
 * @returns {Promise} 返回 [{provinceCode, provinceName, count}, ...]
 */
export const getJobProvinceCount = (jobNames) => {
  return request.post('/achieve/job-province-counts', {
    job_names: jobNames
  })
}

export const getJobSkills = (uid: string) => {
  return request.post('/achieve/job-skills', {
    uid: uid
  })
}

/**
 * 根据专业名、岗位名 和 TopK 获取向量匹配结果（岗位）
 * @param majorName - 专业名称
 * @param jobName - 专业唯一标识
 * @returns Promise<ApiResponse<VectorMatchByUidResponse>>
 */
export const vectorMatchMajorJob = (majorName: string, jobName: string) => {
  return request.post('/achieve/vector-match-major-job', {
    majorName,
    jobName
  })
}

/**
 * 根据专业名、岗位名 和 TopK 获取匹配结果（岗位）
 * @param majorName - 专业名称
 * @param functionName - 专业唯一标识
 * @returns Promise<ApiResponse<VectorMatchByUidResponse>>
 */
export const matchMajorJob = (majorName: string, functionName: string) => {
  return request.post('/achieve/similarity-between', {
    majorName,
    functionName
  })
}

/**
 * 请求匹配解释（为什么这些岗位/专业匹配）
 * @param majorName 专业名称
 * @param functionName 岗位名称
 * @param topK 返回最相似的前 K 个解释结果
 * @param numSamples 每条解释取样的样本数
 */
export const explainMatching = (
  majorName: string, functionName: string, topK: number = 8, numSamples: number = 5
) => {
  return request.post('/achieve/explain-matching', {
    major_name: majorName,
    function_name: functionName,
    top_k: topK,
    num_samples: numSamples,
  })
}

/**
 * 获取领域匹配得分
 * @param majorName 专业名称
 * @param functionName 岗位名称
 * @returns Promise<ApiResponse<DomainMatchingResponse>>
 */
export const getDomainMatching = (majorName: string, functionName: string) => {
  return request.post('/achieve/domain-matching', {
    majorName,
    functionName
  })
}

/**
 * 获取专业-岗位聚合匹配分数（最大值、均值、中位数）
 * @param majorName 专业名称
 * @param functionName 岗位名称
 * @returns Promise<ApiResponse<MatchAggregatedScoreResponse>>
 */
export const getMajorJobAggregatedScore = (majorName: string, functionName: string) => {
  return request.post('/achieve/major-job-aggregated-score', {
    majorName,
    functionName
  })
}

/**
 * 根据岗位 uid 获取岗位技能及出现次数
 * @param uid - 岗位唯一标识
 * @returns Promise<ApiResponse<SkillByUidCountResponse>>
 */
export const getJobSkillsCount = (uid: string) => {
  return request.post('/achieve/job-skills-count', { uid })
}

/**
 * 获取热门专业列表
 * @param limit 返回数量，默认30，范围1-100
 * @returns Promise<ApiResponse<MajorHeatListResponse>>
 */
export const getHotMajors = (limit: number = 30) => {
  return request.get('/achieve/hot-majors', { params: { limit } })
}

/**
 * 获取指定专业的情感分析数据
 * @param major - 专业名称
 * @returns Promise<ApiResponse<SentimentResponse>>
 */
export const getSentimentAnalysis = (major: string) => {
  return request.post('/achieve/sentiment-analysis', { major })
}