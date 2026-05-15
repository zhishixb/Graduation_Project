<template>
  <div class="map-wrapper">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []   // { name: string, value: number }[]
  }
})

const chartRef = ref(null)
let chart = null
let resizeObserver = null
let mapLoaded = false   // 地图是否已注册

// 加载并注册地图（仅一次）
const loadAndRegisterMap = async (mapName) => {
  const response = await fetch(`/maps/${mapName}.geojson`)
  const geoJson = await response.json()
  echarts.registerMap(mapName, geoJson)
}

// 生成图表的配置（data 参数动态传入）
const getOption = (mapName, provinceData) => ({
  backgroundColor: '#F4F6FC',
  tooltip: {
    trigger: 'item',
    backgroundColor: '#fff',
    borderColor: '#6C5CE7',
    borderWidth: 2,
    padding: [10, 15],
    textStyle: { color: '#333', fontSize: 18 },
    formatter: (params) => {
      if (!params.data) return params.name
      return `
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="width:10px;height:10px;background:${params.color};border-radius:50%;"></span>
          <b>${params.name}</b>
        </div>
        <div style="margin-top:6px;">岗位数：${params.data.value}</div>
      `
    }
  },
  visualMap: {
    min: 0,
    max: 90,
    left: 'left',
    top: 'bottom',
    text: ['高', '低'],
    inRange: {
      color: ['#dce3ed', '#5a47e4']
    },
    calculable: true
  },
  geo: [{
    map: mapName,
    aspectScale: 1,
    zoom: 0.9,
    layoutCenter: ['50%', '50%'],
    layoutSize: '100%',
    roam: false,
    label: { show: false },
    itemStyle: {
      areaColor: '#eaf0f6',
      borderColor: '#b0c0d0',
      borderWidth: 1
    },
    emphasis: {
      itemStyle: { areaColor: '#bfd2e6' },
      label: { color: '#1e2a36' }
    }
  }],
  series: [
    // 底部阴影层（保持不变）
    {
      type: 'map', map: mapName, zlevel: -1,
      aspectScale: 1, zoom: 0.9,
      layoutCenter: ['50%', '51.5%'], layoutSize: '100%',
      roam: false, silent: true,
      itemStyle: {
        areaColor: 'rgba(180,190,200,0.4)',
        borderColor: 'rgba(140,155,170,0.6)',
        borderWidth: 1.5,
        shadowColor: 'rgba(0,0,0,0.15)',
        shadowBlur: 20,
        shadowOffsetY: 6
      }
    },
    {
      type: 'map', map: mapName, zlevel: -2,
      aspectScale: 1, zoom: 0.9,
      layoutCenter: ['50%', '53%'], layoutSize: '100%',
      roam: false, silent: true,
      itemStyle: {
        areaColor: 'rgba(150,165,180,0.3)',
        borderColor: 'rgba(120,140,160,0.5)',
        borderWidth: 3,
        shadowColor: 'rgba(0,0,0,0.12)',
        shadowBlur: 30,
        shadowOffsetY: 12
      }
    },
    {
      type: 'map', map: mapName, zlevel: -3,
      aspectScale: 1, zoom: 1.2,
      layoutCenter: ['50%', '54.5%'], layoutSize: '100%',
      roam: false, silent: true,
      itemStyle: {
        areaColor: 'rgba(130,150,170,0.15)',
        borderColor: 'rgba(100,120,145,0.4)',
        borderWidth: 6,
        shadowColor: 'rgba(0,0,0,0.1)',
        shadowBlur: 40,
        shadowOffsetY: 18
      }
    },
    // 数据图层（关键：data 使用传入的 provinceData）
    {
      type: 'map',
      map: mapName,
      zlevel: 0,
      aspectScale: 1,
      zoom: 0.9,
      layoutCenter: ['50%', '50%'],
      layoutSize: '100%',
      roam: false,
      data: provinceData,    // 动态数据
      geoIndex: 0,
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1
      },
      label: { show: false },
      emphasis: {
        label: { show: true, color: '#333' },
        itemStyle: { areaColor: '#FFB3B3' }
      }
    }
  ]
})

// 更新图表数据（只更新第四个 series 的 data）
const updateChartData = (newData) => {
  if (!chart || !mapLoaded) return
  chart.setOption({
    series: [
      {}, {}, {},  // 前三层不变
      { data: newData }
    ]
  })
}

// 监听父组件传递的 data
watch(
  () => props.data,
  (newData) => {
    updateChartData(newData)
  },
  { deep: true }
)

onMounted(async () => {
  chart = echarts.init(chartRef.value)

  // 加载地图 GeoJSON 并注册
  await loadAndRegisterMap('中华人民共和国')
  mapLoaded = true

  // 初始渲染（使用当前 props.data，可能为空）
  chart.setOption(getOption('中华人民共和国', props.data))

  // 监听容器大小变化
  resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(chartRef.value.parentElement)
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<style scoped>
.map-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  border-radius: 12px;
}
.chart {
  width: 100%;
  height: 100%;
}
.chart canvas {
  pointer-events: none !important;
}
</style>