<template>
  <div ref="chartContainer" class="chart-container"></div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  jobDataList: { time: string; count: number }[]
}>()

const chartContainer = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const renderChart = (data: { time: string; count: number }[]) => {
  if (!chartContainer.value) return

  // 销毁旧实例（避免重复初始化）
  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartContainer.value)

  const formatTime = (t: string) => {
    const datePart = t.split(' ')[0].slice(5) // 'MM-DD'
    const timePart = t.split(' ')[1]?.slice(0, 5) || ''
    return `${datePart} ${timePart}`.trim()
  }

  const times = data.map(item => formatTime(item.time))
  const counts = data.map(item => item.count)

  const option = {
    title: {
      text: '岗位数量趋势',
      left: 'center',
      top: 10,
      textStyle: { fontSize: 14, fontWeight: 'normal' }
    },
    tooltip: { trigger: 'axis' },
    legend: { data: ['岗位数量'], bottom: 10, left: 'center' },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: times },
    yAxis: { type: 'value', name: '数量' },
    series: [{
      name: '岗位数量',
      type: 'line',
      smooth: true,
      showSymbol: false,
      areaStyle: {
        opacity: 0.8,
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgb(128, 255, 165)' },
          { offset: 1, color: 'rgb(1, 191, 236)' }
        ])
      },
      data: counts
    }]
  }

  chartInstance.setOption(option)
}

const renderEmptyChart = () => {
  if (!chartContainer.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartContainer.value)
  chartInstance.setOption({
    title: {
      text: '暂无数据',
      left: 'center',
      top: 'center',
      textStyle: { color: '#999' }
    },
    xAxis: { show: false },
    yAxis: { show: false }
  })
}

// 渲染图表：根据传入数据
watch(
  () => props.jobDataList,
  (newData) => {
    if (newData && newData.length > 0) {
      renderChart(newData)
    } else {
      renderEmptyChart()
    }
  },
  { immediate: true }
)

// 组件卸载时清理 ECharts 实例（防止内存泄漏）
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.chart-container {
  width: 500px;
  height: 325px;
  background-color: #fefefe;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>