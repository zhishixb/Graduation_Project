import request from '@/utils/request'

export const cleanMajors = () => {
  return request.get('/api/process/cleanMajor')
}

export const checkMajorStatus = () => {
  return request.get('/api/process/checkMajorStatus')
}
