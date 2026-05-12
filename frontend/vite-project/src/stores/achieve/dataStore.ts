import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useDataStore = defineStore('dataStore', () => {
  // 当前页面标识（唯一需要手动更新的状态）
  const nowPage = ref('dashBoard')

  // 独立的布尔变量，完全由 nowPage 自动计算
  const toDashBoard = computed(() => nowPage.value === 'dashBoard')
  const toMajorDetail = computed(() => nowPage.value === 'majorDetail')
  const toPositionDetail = computed(() => nowPage.value === 'positionDetail')
  const toComparePage = computed(() => nowPage.value === 'comparePage')
  const toHotMajor = computed(() => nowPage.value === 'hotMajor')

  // 加载标志
  const isLoading = ref(false)

  // 数据传递
  const majorName = ref('专业名')
  const jobName = ref('岗位名')

  // 页面切换方法
  const turnToPage = (pageName: string) => {
    nowPage.value = pageName
      isLoading.value = true
  }

  // 数据改变方法
  const selectMajorName = (newMajorName : string) => {
    majorName.value = newMajorName
  }

  const selectJobName = (newJobName : string) => {
    jobName.value = newJobName
  }

  const getterMajorName = () => {
    return majorName.value
  }

  const getterJobName = () => {
    return jobName.value
  }

  return {
    nowPage,
    toDashBoard,
    toMajorDetail,
    toPositionDetail,
    toComparePage,
    toHotMajor,
    turnToPage,
    selectMajorName,
    selectJobName,
    getterMajorName,
    getterJobName,
    isLoading,
  }
})