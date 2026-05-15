<template>
  <div ref="chartRef" :style="{ width: width + 'px', height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

interface WordItem {
  name: string
  value: number
}

const props = withDefaults(defineProps<{
  data: WordItem[]
  width?: number
  height?: number
}>(), {
  width: 360,
  height: 280
})

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const renderChart = () => {
  if (!chartRef.value || props.data.length === 0) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option = {
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      sizeRange: [14, 60],
      rotationRange: [-90, 90],
      rotationStep: 45,
      gridSize: 8,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: () => {
          const colors = ['#1677ff', '#52c41a', '#fa541c', '#722ed1', '#13c2c2', '#eb2f96']
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      emphasis: {
        textStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' }
      },
      data: props.data
    }]
  }
  chartInstance.setOption(option)
}

// 监听尺寸变化，自动 resize
watch([() => props.width, () => props.height], () => {
  if (chartInstance && !chartInstance.isDisposed()) {
    // 延迟一点确保容器已重新渲染
    setTimeout(() => chartInstance?.resize(), 0)
  }
})

// 监听数据变化，重新渲染
watch(() => props.data, renderChart, { deep: true })

onMounted(() => {
  renderChart()
})

onBeforeUnmount(() => {
  chartInstance?.dispose()
})
</script>