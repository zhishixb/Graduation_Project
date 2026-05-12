import { defineStore } from 'pinia'

export const useBusinessStore = defineStore('businessStore', () => {

  // 专业级联树构建（保持不变）
  const buildMajorCascaderTree = (rawData) => {
    const tree = []
    for (const [categoryName, subCategories] of Object.entries(rawData)) {
      const children = []
      for (const [subCategoryName, majors] of Object.entries(subCategories)) {
        const subChildren = []
        for (const [majorKey, majorInfo] of Object.entries(majors)) {
          const majorName = majorInfo.major_name || majorKey
          subChildren.push({
            label: majorName,
            value: majorName,
          })
        }
        if (subChildren.length > 0) {
          children.push({
            label: subCategoryName,
            value: subCategoryName,
            children: subChildren
          })
        }
      }
      if (children.length > 0) {
        tree.push({
          label: categoryName,
          value: categoryName,
          children
        })
      }
    }
    return tree
  }

  // 岗位级联树构建（保持不变）
  const buildCascaderOptions = (jobData) => {
    const options = [];
    for (const [category, subCategories] of Object.entries(jobData)) {
      const categoryChildren = [];
      for (const [subCategory, jobs] of Object.entries(subCategories)) {
        const subChildren = [];
        for (const [jobName, jobInfo] of Object.entries(jobs)) {
          subChildren.push({
            label: jobName,
            value: jobInfo.uid
          });
        }
        if (subChildren.length > 0) {
          categoryChildren.push({
            label: subCategory,
            value: subCategory,
            children: subChildren
          });
        }
      }
      if (categoryChildren.length > 0) {
        options.push({
          label: category,
          value: category,
          children: categoryChildren
        });
      }
    }
    return options;
  }

  /**
   * 将后端返回的含索引的词对数据转换为热力图可用的语义对数组
   * @param data - 原始数据对象，包含 tokens_a, tokens_b, echarts_data
   * @returns 语义对数组，每项形如 { word1, word2, score }
   */
  const transformToSemanticPairs = (
    data: {
      tokens_a: string[]
      tokens_b: string[]
      echarts_data: number[][]
    }
  ): Array<{ word1: string; word2: string; score: number }> => {
    if (!data || !Array.isArray(data.tokens_a) || !Array.isArray(data.tokens_b) || !Array.isArray(data.echarts_data)) {
      return []
    }

    const { tokens_a, tokens_b, echarts_data } = data

    return echarts_data.map(([iA, iB, score]) => {
      const word1 = tokens_a[iA] ?? `词A${iA}`
      const word2 = tokens_b[iB] ?? `词B${iB}`
      return {word1, word2, score: typeof score === 'number' ? score : 0
      }
    })
  }

  return {
    buildMajorCascaderTree,
    buildCascaderOptions,
    transformToSemanticPairs
  }
})