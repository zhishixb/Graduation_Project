<template>
  <div class="map-wrapper">
    <div ref="chartRef" class="chart"></div>

    <!-- 自定义 Vue 标记：使用气泡组件 -->
    <div
      v-for="(marker, index) in markerPixels"
      :key="marker.name"
      class="custom-marker"
      :style="{ left: marker.x + 'px', top: marker.y + 'px' }"
    >
      <MapBubble
        :icon-component="marker.icon"
        :label-text="marker.text"
        :color="marker.color"
        :color-end="marker.colorEnd"
        :shadow-opacity="marker.shadowOpacity"
        :shadow-opacity-hover="marker.shadowOpacityHover"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import MapBubble from '@/components/graduation_project/achieve/page/dash_board/BubbleMarker.vue'
// 导入所需的图标组件（示例：ionicons5）
import {Bulb, Planet, Journal } from '@vicons/ionicons5'

/* ---------- 标记内容数组（图标 + 悬停展示文字 + 颜色） ---------- */
const markerContents = [
  {
    icon: Bulb,
    text: '热门专业',
    color: '#FF6B6B',      // 渐变起始色
    colorEnd: '#EE5A24'    // 渐变结束色 / 箭头色
  },
  {
    icon: Planet,
    text: '岗位专业对比',
    color: '#54A0FF',
    colorEnd: '#5F27CD'
  },
  {
    icon: Journal,
    text: '全部专业',
    color: '#10AC84',
    colorEnd: '#1DD1A1'
  }
]

const chartRef = ref(null)
let chart = null

const markerPixels = ref([])
const selectedGeoCoords = ref([])

/* ---------- 几何工具函数（计算区域中心、距离、分散选点） ---------- */
const getRegionCenter = (geoJson, regionName) => {
  const feature = geoJson.features.find(f => f.properties.name === regionName)
  if (!feature || !feature.geometry) return null

  const { type, coordinates } = feature.geometry

  if (type === 'Polygon') {
    const ring = coordinates[0]
    let x = 0, y = 0
    ring.forEach(p => { x += p[0]; y += p[1] })
    return [x / ring.length, y / ring.length]
  }

  if (type === 'MultiPolygon') {
    let totalX = 0, totalY = 0, count = 0
    coordinates.forEach(polygon => {
      const ring = polygon[0]
      ring.forEach(p => { totalX += p[0]; totalY += p[1]; count++ })
    })
    return count ? [totalX / count, totalY / count] : null
  }

  return null
}

const distance = (a, b) => Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

const selectDispersedRegions = (points, k = 3) => {
  if (points.length <= k) return [...points]

  const shuffled = [...points].sort(() => Math.random() - 0.5)
  const selected = [shuffled[0]]
  const remaining = shuffled.slice(1)

  let maxDist = -1, bestIdx = -1
  remaining.forEach((p, i) => {
    const d = distance(selected[0].coord, p.coord)
    if (d > maxDist) { maxDist = d; bestIdx = i }
  })
  selected.push(remaining[bestIdx])
  remaining.splice(bestIdx, 1)

  let bestMinDist = -1
  bestIdx = -1
  remaining.forEach((p, i) => {
    const minDist = Math.min(...selected.map(s => distance(s.coord, p.coord)))
    if (minDist > bestMinDist) { bestMinDist = minDist; bestIdx = i }
  })
  if (bestIdx !== -1) selected.push(remaining[bestIdx])

  return selected
}

/* ---------- 坐标转换 & 绑定内容 ---------- */
const updateMarkerPositions = () => {
  if (!chart || !selectedGeoCoords.value.length) {
    markerPixels.value = []
    return
  }

  const pixels = selectedGeoCoords.value
    .map((item, index) => {
      const pixel = chart.convertToPixel({ geoIndex: 0 }, item.coord)
      if (isNaN(pixel[0]) || isNaN(pixel[1])) return null

      // 按索引从数组中取内容，循环使用
      const content = markerContents[index % markerContents.length]

      return {
        name: item.name,
        x: pixel[0],
        y: pixel[1],
        icon: content.icon,
        text: content.text,
        color: content.color || '#a0c4ff',
        colorEnd: content.colorEnd || '#bdb2ff',
        shadowOpacity: content.shadowOpacity || 0.4,
        shadowOpacityHover: content.shadowOpacityHover || 0.5
      }
    })
    .filter(Boolean)

  markerPixels.value = pixels
}

/* ---------- 加载地图并渲染 ECharts ---------- */
const loadAndRenderMap = async (mapName) => {
  const response = await fetch(`/maps/${mapName}.geojson`)
  const geoJson = await response.json()
  echarts.registerMap(mapName, geoJson)

  const allRegions = geoJson.features
    .map(f => {
      const name = f.properties.name
      if (!name) return null
      const coord = getRegionCenter(geoJson, name)
      return coord ? { name, coord } : null
    })
    .filter(Boolean)

  const selected = selectDispersedRegions(allRegions, 3)
  selectedGeoCoords.value = selected

  const option = {
    backgroundColor: '#F4F6FC',
    geo: [{
      map: mapName,
      aspectScale: 1,
      zoom: 0.9,
      layoutCenter: ['50%', '50%'],
      layoutSize: '100%',
      roam: false,
      label: { show: true, color: '#3a4a5c', fontSize: 11 },
      itemStyle: {
        areaColor: {
          type: 'linear', x: 0, y: 0, x2: 1, y2: 1,
          colorStops: [
            { offset: 0, color: '#dce3ed' },
            { offset: 1, color: '#eaf0f6' }
          ],
          global: false
        },
        borderColor: '#b0c0d0',
        borderWidth: 1
      },
      emphasis: {
        itemStyle: { areaColor: '#bfd2e6' },
        label: { color: '#1e2a36' }
      }
    }],
    series: [
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
      }
    ]
  }

  chart.off('finished', updateMarkerPositions)
  chart.on('finished', updateMarkerPositions)
  chart.setOption(option, true)
}

onMounted(async () => {
  chart = echarts.init(chartRef.value)
  await loadAndRenderMap('杭州市')
  window.addEventListener('resize', () => {
    chart?.resize()
    updateMarkerPositions()
  })
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', updateMarkerPositions)
})
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: #f4ebf9;
  overflow: hidden;
}

.chart {
  width: 100%;
  height: 100%;
  z-index: -1;
}

.chart canvas {
  pointer-events: none !important;
}

.custom-marker {
  position: absolute;
  transform: translate(-50%, -100%);
  pointer-events: auto;
  cursor: pointer;
  z-index: 100;
}
</style>