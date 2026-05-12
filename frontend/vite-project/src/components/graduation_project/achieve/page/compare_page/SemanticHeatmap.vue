<template>
  <div class="heatmap-wrapper" :style="{ width: width + 'px', height: height + 'px' }">
    <div ref="chartRef" class="heatmap-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = withDefaults(defineProps<{
  data: any[]
  width?: number
  height?: number
}>(), {
  width: 450,
  height: 400
})

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null
let isMounted = false

const formattedData = (): Array<{ word1: string; word2: string; score: number }> => {
  if (!Array.isArray(props.data)) return []
  return props.data.map(item => {
    if (Array.isArray(item)) {
      return { word1: item[0], word2: item[1], score: item[2] }
    }
    return item as { word1: string; word2: string; score: number }
  })
}

const setChartOption = () => {
  if (!chartInstance || chartInstance.isDisposed() || !isMounted) return

  const list = formattedData()
  const xWords = [...new Set(list.map(d => d.word2).filter(Boolean))]
  const yWords = [...new Set(list.map(d => d.word1).filter(Boolean))]
  const xIndexMap = new Map(xWords.map((w, i) => [w, i]))
  const yIndexMap = new Map(yWords.map((w, i) => [w, i]))
  const seriesData = list.map(d => {
    const xi = xIndexMap.get(d.word2)
    const yi = yIndexMap.get(d.word1)
    if (xi === undefined || yi === undefined) return null
    return [xi, yi, d.score]
  }).filter(Boolean) as number[][]

  // 密集颜色数组，使低值和高值均有清晰区分
  const colorRange = [
    '#f0f9e8', '#ccebc5', '#a8ddb5', '#7bccc4', '#4eb3d3', // 0.0~0.4
    '#2b8cbe', '#0868ac',                                   // 0.4~0.6
    '#fff7bc', '#fee391', '#fec44f', '#fe9929',             // 0.6~0.8
    '#ec7014', '#cc4c02', '#993404', '#7f2704',             // 0.8~0.95
    '#5c1400', '#3b0a00'                                    // 0.95~1.0
  ]

  const option = {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const [xi, yi, val] = params.value || []
        return `${yWords[yi] || ''} ↔ ${xWords[xi] || ''}<br/>相似度: ${val?.toFixed(4)}`
      }
    },
    grid: { left: 60, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: 'category',
      data: xWords,
      axisLabel: { rotate: 30, fontSize: 11 },
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: yWords,
      axisLabel: { fontSize: 11 },
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { fontSize: 10 },
      inRange: {
        color: colorRange
      }
    },
    series: [{
      type: 'heatmap',
      data: seriesData,
      label: {
        show: true,
        fontSize: 10,
        formatter: (params: any) => params.value[2]?.toFixed(2) || ''
      },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      }
    }]
  }
  chartInstance.setOption(option)
}

const safeSetOption = () => {
  if (chartInstance && !chartInstance.isDisposed() && isMounted) {
    setChartOption()
  }
}

const initChart = () => {
  if (!chartRef.value || !isMounted) return
  chartInstance = echarts.init(chartRef.value)
  setChartOption()
}

const handleResize = () => {
  if (chartInstance && !chartInstance.isDisposed() && isMounted) {
    chartInstance.resize()
  }
}

watch(() => props.data, () => {
  safeSetOption()
}, { deep: true })

onMounted(() => {
  isMounted = true
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  isMounted = false
  window.removeEventListener('resize', handleResize)
  if (chartInstance && !chartInstance.isDisposed()) {
    chartInstance.dispose()
  }
  chartInstance = null
})
</script>

<style scoped>
.heatmap-wrapper {
  box-sizing: border-box;
}
.heatmap-chart {
  width: 100%;
  height: 100%;
}
</style>