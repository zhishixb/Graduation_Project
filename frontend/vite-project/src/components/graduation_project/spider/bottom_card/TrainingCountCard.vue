<template>
  <div class="chart-wrapper">
    <!-- Loading 状态 -->
    <div v-if="loading" class="loading-state">
      <n-spin size="large" description="正在加载训练数据..." />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <n-result status="500" title="数据加载失败" :description="error">
        <template #footer>
          <n-button @click="fetchData">重试</n-button>
        </template>
      </n-result>
    </div>

    <!-- 图表容器 -->
    <div
      ref="chartContainer"
      class="chart-container"
      v-show="!loading && !error"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import * as echarts from 'echarts';
import { getTrainingDataList } from "@/apis/spider";
import { NSpin, NResult, NButton } from 'naive-ui';

// --- 配置常量 (已更新高度为 320) ---
const FIXED_WIDTH = 480;
const FIXED_HEIGHT = 320;

// --- 状态定义 ---
const chartContainer = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;
const loading = ref(false);
const error = ref<string | null>(null);

// --- 核心逻辑：获取数据并渲染 ---
const fetchData = async () => {
  loading.value = true;
  error.value = null;

  try {
    const res = await getTrainingDataList();
    const rawData = Array.isArray(res) ? res : (res.data || res.ta || []);

    if (!rawData || rawData.length === 0) {
      throw new Error("未获取到有效数据");
    }

    const dates = rawData.map((item: any[]) => {
      const dateStr = item[0];
      return dateStr ? dateStr.split('T')[0].substring(5) : '';
    });

    const values = rawData.map((item: any[]) => item[1] || 0);

    await nextTick();
    renderChart(dates, values);

  } catch (err: any) {
    console.error("Failed to fetch training data:", err);
    error.value = err.message || "网络异常，请稍后重试";
  } finally {
    loading.value = false;
  }
};

// --- ECharts 渲染逻辑 ---
const renderChart = (categories: string[], values: number[]) => {
  if (!chartContainer.value) return;

  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }

  // 【关键】强制初始化尺寸为 480x320
  chartInstance = echarts.init(chartContainer.value, null, {
    width: FIXED_WIDTH,
    height: FIXED_HEIGHT,
    devicePixelRatio: window.devicePixelRatio || 1
  });

  const option = {
    color: ['#80FFA5', '#00DDFF', '#37A2FF', '#FF0087', '#FFBF00'],
    title: {
      text: '训练数据增长趋势',
      left: 'center',
      top: 6, // 进一步压缩顶部距离
      textStyle: { color: '#333', fontSize: 13 } // 字体稍小
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
      formatter: (params: any) => {
        const dateFull = categories[params[0].dataIndex];
        return `<strong>${dateFull}</strong><br/>数据量: ${params[0].value}`;
      }
    },
    legend: {
      data: ['训练数据量'],
      bottom: 0, // 紧贴底部
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { fontSize: 10 } // 字体缩小
    },
    toolbox: {
      feature: {
        saveAsImage: { title: '保存', pixelRatio: 2 },
        magicType: { title: { line: '折线', bar: '柱状' }, type: ['line', 'bar'] },
        dataZoom: { title: { zoom: '缩放', back: '还原' } }
      },
      right: 4,
      top: 4,
      iconSize: 12 // 图标缩小
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%', // 减少底部留白给图例腾空间
      top: '12%',    // 减少顶部留白
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: false,
        data: categories,
        axisLine: { lineStyle: { color: '#eee' } },
        axisLabel: { color: '#666', fontSize: 9 } // X轴字体缩小
      }
    ],
    yAxis: [
      {
        type: 'value',
        splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } },
        axisLabel: { color: '#666', fontSize: 9 } // Y轴字体缩小
      }
    ],
    series: [
      {
        name: '训练数据量',
        type: 'line',
        stack: 'Total',
        smooth: true,
        lineStyle: { width: 0 },
        showSymbol: false,
        areaStyle: {
          opacity: 0.8,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgb(128, 255, 165)' },
            { offset: 1, color: 'rgb(1, 191, 236)' }
          ])
        },
        emphasis: { focus: 'series' },
        data: values
      }
    ]
  };

  chartInstance.setOption(option);
  chartInstance.resize({ width: FIXED_WIDTH, height: FIXED_HEIGHT });
};

// --- 生命周期 ---
onMounted(() => {
  fetchData();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize({ width: FIXED_WIDTH, height: FIXED_HEIGHT });
  }
};
</script>

<style scoped>
.chart-wrapper {
  /* 强制固定尺寸 480x320 */
  width: 480px !important;
  height: 320px !important;

  position: relative;
  flex-shrink: 0 !important;
  flex-grow: 0 !important;
  margin: 0 auto;

  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.chart-container {
  width: 100%;
  height: 100%;
  display: block;
}

.loading-state,
.error-state {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10;
  background: rgba(255,255,255,0.95);
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>