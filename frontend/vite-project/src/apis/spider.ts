import request from '@/utils/request'

export const getMajorsList = () => {
  return request.get('/api/spider/allMajors')
}

export const getJobList = () => {
  return request.get('/api/spider/allJobs')
}

export const getTrainingDataList = () => {
  return request.get('/api/spider/getTrainingDataCount')
}