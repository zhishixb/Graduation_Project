<template>
  <div class="radar-wrapper" :style="{ width: width + 'px', height: height + 'px' }">
    <div ref="chartRef" class="radar-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface DomainItem {
  category: string
  score: number
}

const props = withDefaults(defineProps<{
  data: DomainItem[]
  width?: number
  height?: number
}>(), {
  width: 450,
  height: 400
})

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null
let isMounted = false

const buildOption = (): echarts.EChartsOption => {
  const list = props.data || []
  console.log('[DomainRadar] 构建配置，当前数据长度:', list.length)
  return {
    tooltip: { trigger: 'item' },
    radar: {
      indicator: list.map(d => ({ name: d.category, max: 1 })),
      center: ['50%', '55%'],
      radius: '65%',
      axisName: { fontSize: 11, color: '#555' }
    },
    series: [{
      type: 'radar',
      data: [{
        value: list.map(d => d.score),
        name: '领域匹配度',
        areaStyle: { opacity: 0.25, color: '#1677ff' },
        lineStyle: { color: '#1677ff', width: 2 },
        itemStyle: { color: '#1677ff' }
      }]
    }]
  }
}

const setChartOption = () => {
  if (!chartInstance || chartInstance.isDisposed() || !isMounted) {
    console.warn('[DomainRadar] 无法设置配置，实例状态:', { chartInstance, isMounted })
    return
  }
  chartInstance.setOption(buildOption())
  console.log('[DomainRadar] 配置已应用')
}

const initChart = () => {
  if (!chartRef.value || !isMounted) return
  console.log('[DomainRadar] 初始化图表')
  chartInstance = echarts.init(chartRef.value)
  setChartOption()
}

const handleResize = () => {
  if (chartInstance && !chartInstance.isDisposed() && isMounted) {
    chartInstance.resize()
  }
}

watch(() => props.data, () => {
  console.log('[DomainRadar] 数据变化，更新图表')
  setChartOption()
}, { deep: true })

onMounted(() => {
  isMounted = true
  console.log('[DomainRadar] 组件挂载，当前数据:', props.data)
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
.radar-wrapper {
  box-sizing: border-box;
}
.radar-chart {
  width: 100%;
  height: 100%;
}
</style>