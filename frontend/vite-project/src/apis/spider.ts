import request from '@/utils/request'

export const getMajorsList = () => {
  return request.get('/spider/allMajors')
}

export const getJobList = () => {
  return request.get('/spider/allJobs')
}

export const getMajorList = () => {
  return request.get('/spider/allMajor')
}

export const getTrainingDataList = () => {
  return request.get('/spider/getTrainingDataCount')
}