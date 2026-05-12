// src/utils/request.ts
import axios from 'axios';

// 创建 Axios 实例
const http = axios.create({
  baseURL: '/api',
  timeout: 600000,
});

// 统一请求函数
async function request<T = any>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  url: string,
  config: any = {}
): Promise<T> {
  try {
    const response = await http.request({
      method,
      url,
      ...config,
    });
    return response.data;
  } catch (error: any) {
    // 统一错误提示（使用 Naive UI message）
    const msg = error.response?.data?.message || '请求失败，请稍后再试'
    console.log(msg)
    return Promise.reject(error);
  }
}

export default {
  get<T = any>(url: string, params?: Record<string, any>): Promise<T> {
    return request('GET', url, { params });
  },
  post<T = any>(url: string, data?: any): Promise<T> {
    return request('POST', url, { data });
  },
  put<T = any>(url: string, data?: any): Promise<T> {
    return request('PUT', url, { data });
  },
  delete<T = any>(url: string): Promise<T> {
    return request('DELETE', url);
  },
};