import request from '@/utils/request'

export const cleanMajors = () => {
  return request.get('/process/cleanMajor')
}

export const checkMajorStatus = () => {
  return request.get('/process/checkMajorStatus')
}
