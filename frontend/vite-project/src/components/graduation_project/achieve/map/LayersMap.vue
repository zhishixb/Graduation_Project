<template>
  <div class="map-container">
    <button v-if="mapStack.length > 1" class="back-btn" @click="goBack">
      ← 返回上级
    </button>
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';

const chartRef = ref(null);
let chart = null;
const mapStack = ref(['100000']); // 初始为中国

//-------------------------------------------------------------------------
// 加载 GeoJSON 并渲染带阴影的立体地图
//-------------------------------------------------------------------------
const loadAndRenderMap = async (mapName) => {
  const response = await fetch(`/maps/${mapName}.geojson`);
  const geoJson = await response.json();
  echarts.registerMap(mapName, geoJson);

  const option = {
    // 🌌 深色背景，让阴影可见
    backgroundColor: '#040d21',

    // 主体地图 (geo 作为主显示层)
    geo: [
      {
        map: mapName,
        aspectScale: 1,
        zoom: 0.9,
        layoutCenter: ['50%', '50%'],
        layoutSize: '100%',
        roam: true,
        label: {
          show: true,
          color: '#a0c5e8',
          fontSize: 11,
        },
        itemStyle: {
          areaColor: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 1,
            colorStops: [
              { offset: 0, color: '#0b1f4a' },
              { offset: 1, color: '#1b4f8a' },
            ],
            global: false,
          },
          borderColor: 'rgba(100,180,255,0.6)',
          borderWidth: 1,
        },
        emphasis: {
          itemStyle: {
            areaColor: '#2e6fbd',
          },
          label: {
            color: '#fff',
          },
        },
      },
    ],

    // 📦 多层阴影系列 (通过 zlevel 控制层级，不绑定 geoIndex 以免覆盖)
    series: [
      // 第一层阴影（紧贴地图）
      {
        type: 'map',
        map: mapName,
        zlevel: -1,           // 在 geo 下方
        aspectScale: 1,
        zoom: 0.9,
        layoutCenter: ['50%', '51.5%'], // 向下偏移
        layoutSize: '100%',
        roam: false,
        silent: true,
        itemStyle: {
          areaColor: 'rgba(10,30,70,0.7)',  // 更深的颜色，可见
          borderColor: 'rgba(58,149,253,0.7)',
          borderWidth: 1.5,
          shadowColor: 'rgba(0,180,255,0.8)',
          shadowBlur: 20,
          shadowOffsetY: 6,
        },
      },
      // 第二层阴影（更远）
      {
        type: 'map',
        map: mapName,
        zlevel: -2,
        aspectScale: 1,
        zoom: 0.9,
        layoutCenter: ['50%', '53%'],
        layoutSize: '100%',
        roam: false,
        silent: true,
        itemStyle: {
          areaColor: 'rgba(5,15,50,0.6)',
          borderColor: 'rgba(29,111,165,0.7)',
          borderWidth: 3,
          shadowColor: 'rgba(0,140,255,0.8)',
          shadowBlur: 30,
          shadowOffsetY: 12,
        },
      },
      // 第三层阴影（最外层光晕）
      {
        type: 'map',
        map: mapName,
        zlevel: -3,
        aspectScale: 1,
        zoom: 1.2,
        layoutCenter: ['50%', '54.5%'],
        layoutSize: '100%',
        roam: false,
        silent: true,
        itemStyle: {
          areaColor: 'rgba(5,15,50,0.3)',
          borderColor: 'rgba(0,100,200,0.5)',
          borderWidth: 6,
          shadowColor: 'rgba(0,200,255,0.9)',
          shadowBlur: 40,
          shadowOffsetY: 18,
        },
      },
    ],
  };

  chart.setOption(option, true);
};

//-------------------------------------------------------------------------
// 点击下钻
//-------------------------------------------------------------------------
const handleMapClick = (params) => {
  tryLoadNextLevel(params.name);
};

const tryLoadNextLevel = async (regionName) => {
  try {
    const res = await fetch(`/maps/${regionName}.geojson`);
    if (!res.ok) {
      console.warn(`未找到 ${regionName}.geojson`);
      return;
    }
    mapStack.value.push(regionName);
    await loadAndRenderMap(regionName);
  } catch (e) {
    console.warn(`加载失败: ${regionName}.geojson`, e);
  }
};

//-------------------------------------------------------------------------
// 返回上级
//-------------------------------------------------------------------------
const goBack = () => {
  if (mapStack.value.length <= 1) return;
  mapStack.value.pop();
  const prev = mapStack.value[mapStack.value.length - 1];
  loadAndRenderMap(prev);
};

//-------------------------------------------------------------------------
// 生命周期
//-------------------------------------------------------------------------
onMounted(async () => {
  chart = echarts.init(chartRef.value);
  chart.on('click', handleMapClick);
  await loadAndRenderMap('100000');
  window.addEventListener('resize', () => chart?.resize());
});

onUnmounted(() => {
  chart?.off('click', handleMapClick);
  chart?.dispose();
});
</script>

<style scoped>
.map-container {
  position: relative;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: #040d21;     
  overflow: hidden;        /* 👈 加上这一行，裁剪内部 canvas 的四个角 */
}
.back-btn {
  position: absolute;
  top: 15px;
  left: 15px;
  z-index: 20;
  padding: 6px 18px;
  background: rgba(0,20,50,0.8);
  border: 1px solid #4ea5d9;
  color: #d6eeff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  backdrop-filter: blur(4px);
}
.back-btn:hover {
  background: rgba(10,40,80,0.9);
}
.chart {
  width: 100%;
  height: 600px;
}
</style>