<template>
  <div class="chart-wrapper">
    <!-- Loading 状态 -->
    <div v-if="loading" class="loading-state">
      <n-spin size="large" description="正在加载数据..." />
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

// --- 配置常量 ---
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
    const rawData = res?.data || res;

    if (!rawData || typeof rawData !== 'object') {
      throw new Error("数据格式无效");
    }

    // 1. 提取所有日期并排序
    const allDatesSet = new Set<string>();
    Object.values(rawData).forEach((seriesData: any[]) => {
      seriesData.forEach((item: any[]) => {
        if (item[0]) {
          const dateStr = item[0].split('T')[0].substring(5);
          allDatesSet.add(dateStr);
        }
      });
    });

    const categories = Array.from(allDatesSet).sort((a, b) => {
      return new Date(`2026-${a}`).getTime() - new Date(`2026-${b}`).getTime();
    });

    // 2. 数据对齐与填充 (用前一天数据补全)
    const seriesDataMap: Record<string, number[]> = {};

    // 定义明确的渲染顺序：先 BOSS (底层)，后 51job (顶层)
    // ECharts 堆叠顺序 = 数组索引顺序 (索引 0 在最底)
    const renderOrder = ['boss', '51job'];

    renderOrder.forEach(platform => {
      if (!rawData[platform]) return;

      const platformData = rawData[platform];
      const dataMap = new Map<string, number>();

      platformData.forEach((item: any[]) => {
        const dateStr = item[0].split('T')[0].substring(5);
        dataMap.set(dateStr, item[1] || 0);
      });

      const filledData: number[] = [];
      let lastValidValue = 0;

      categories.forEach(date => {
        if (dataMap.has(date)) {
          lastValidValue = dataMap.get(date)!;
        }
        filledData.push(lastValidValue);
      });

      seriesDataMap[platform] = filledData;
    });

    await nextTick();
    renderChart(categories, seriesDataMap, renderOrder);

  } catch (err: any) {
    console.error("Failed to fetch training data:", err);
    error.value = err.message || "网络异常，请稍后重试";
  } finally {
    loading.value = false;
  }
};

// --- ECharts 渲染逻辑 (优化配色 + 调整顺序) ---
const renderChart = (categories: string[], seriesMap: Record<string, number[]>, order: string[]) => {
  if (!chartContainer.value) return;

  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }

  chartInstance = echarts.init(chartContainer.value, null, {
    width: FIXED_WIDTH,
    height: FIXED_HEIGHT,
    devicePixelRatio: window.devicePixelRatio || 1
  });

  // 🎨 全新配色方案
  // 底层 (BOSS): 深紫 -> 蔚蓝 (稳重、科技感)
  const bossGradient = {
    start: '#27459c',
    end: '#bc67c5'
  };
  // 顶层 (51Job): 青绿 -> 亮蓝 (活力、增长)
  const job51Gradient = {
    start: '#00f260',
    end: '#0575e6'
  };

  const seriesList = order.map((platform) => {
    let nameDisplay = '';
    let gradientConfig = { start: '#ccc', end: '#eee' };

    if (platform === 'boss') {
      nameDisplay = 'BOSS直聘';
      gradientConfig = bossGradient;
    } else if (platform === '51job') {
      nameDisplay = '51Job';
      gradientConfig = job51Gradient;
    }

    return {
      name: nameDisplay,
      type: 'line',
      stack: 'Total', // 保持堆叠
      smooth: true,
      lineStyle: {
        width: 0 // 隐藏线条，纯面积展示
      },
      showSymbol: false,
      areaStyle: {
        opacity: 0.9, // 稍微提高不透明度，让颜色更实
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: gradientConfig.start },
          { offset: 1, color: gradientConfig.end }
        ])
      },
      emphasis: {
        focus: 'series',
        areaStyle: {
          opacity: 1.0 // 鼠标悬停时完全不透明
        }
      },
      data: seriesMap[platform] || []
    };
  });

  const option = {
    backgroundColor: '#fff', // 确保背景纯白
    title: {
      text: '岗位总量爬取总量',
      left: 'center',
      top: 8,
      textStyle: {
        color: '#2c3e50',
        fontSize: 14,
        fontWeight: 'bold',
        fontFamily: 'sans-serif'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#2c3e50',
          borderColor: '#2c3e50',
          borderWidth: 0,
          color: '#fff',
          padding: [4, 8],
          borderRadius: 4
        }
      },
      formatter: (params: any[]) => {
        let total = 0;
        params.forEach(p => total += p.value);

        // 标题显示总日期和总量
        let html = `<div style="font-weight:bold; margin-bottom:6px; font-size:13px;">${params[0].name} <span style="font-weight:normal; font-size:12px; opacity:0.8">(总计: ${total >= 10000 ? (total/10000).toFixed(2)+'w' : total})</span></div>`;

        // 列表显示各平台
        params.forEach(p => {
          let valDisplay = p.value;
          if (p.value >= 10000) valDisplay = (p.value / 10000).toFixed(2) + 'w';

          html += `<div style="display:flex; justify-content:space-between; align-items:center; width:150px; margin-top:4px;">
            <span style="display:flex; align-items:center;">
              <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:6px;box-shadow:0 0 4px rgba(0,0,0,0.2);"></span>
              <span style="color:#555; font-size:12px;">${p.seriesName}</span>
            </span>
            <span style="font-weight:bold; color:#2c3e50; font-size:13px;">${valDisplay}</span>
          </div>`;
        });
        return html;
      }
    },
    legend: {
      data: seriesList.map((s: any) => s.name),
      bottom: 2, // 稍微离底部一点距离
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: {
        fontSize: 11,
        color: '#555',
        fontWeight: 'bold'
      },
      padding: [0, 0, 0, 0]
    },
    toolbox: {
      feature: {
        saveAsImage: {
          title: '保存',
          pixelRatio: 2,
          iconStyle: { borderColor: '#999' }
        },
        magicType: {
          title: { line: '折线', bar: '柱状' },
          type: ['line', 'bar']
        }
      },
      right: 8,
      top: 8,
      iconSize: 14
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%', // 给图例留足空间
      top: '15%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: false,
        data: categories,
        axisLine: {
          lineStyle: { color: '#e0e0e0', width: 1 }
        },
        axisTick: { show: false },
        axisLabel: {
          color: '#888',
          fontSize: 10,
          interval: 'auto',
          margin: 10
        }
      }
    ],
    yAxis: [
      {
        type: 'value',
        splitLine: {
          lineStyle: {
            type: 'dashed',
            color: '#f0f0f0',
            width: 1
          }
        },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#888',
          fontSize: 10,
          formatter: (value: number) => {
            if (value >= 10000) return (value / 10000).toFixed(0) + 'w';
            return value.toString();
          }
        },
        min: 0
      }
    ],
    series: seriesList
  };

  chartInstance.setOption(option);
  chartInstance.resize({ width: FIXED_WIDTH, height: FIXED_HEIGHT });
};

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
  width: 480px !important;
  height: 320px !important;
  position: relative;
  flex-shrink: 0 !important;
  flex-grow: 0 !important;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 12px; /* 圆角稍微大一点，更现代 */
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06); /* 阴影更柔和 */
  overflow: hidden;
  border: 1px solid #f5f5f5;
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
  background: rgba(255,255,255,0.98);
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>