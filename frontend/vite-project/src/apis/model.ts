import request from '@/utils/request'

// --- 1. 定义请求参数的类型 (对应后端的 ModelCompareRequest) ---
export interface ModelCompareParams {
  model_a: string;       // 第一个模型名称
  model_b: string;       // 第二个模型名称
  major: string;         // 专业名称
  jobs: string[];        // 岗位列表
}

// --- 2. 获取模型列表 (GET) ---
export const getModelList = () => {
  return request.get('/models/getModelList')
}

// --- 3. 双模型对比 (POST) ---
export const compareModels = (data: ModelCompareParams) => {
  return request.post('/models/modelCompare', data)
}