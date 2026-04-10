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
          const dateStr = item[0].split('T')[0];
          allDatesSet.add(dateStr);
        }
      });
    });

    const categories = Array.from(allDatesSet).sort();

    // 2. 准备数据
    const seriesDataMap: Record<string, number[]> = {};

    // 定义所有可能的平台
    const allPlatforms = ['boss', '51position', '51job'];

    // 平台显示配置
    const platformConfig: Record<string, { name: string; start: string; end: string }> = {
      '51position': {
        name: '51Position',
        start: '#f093fb',
        end: '#f5576c'
      },
      'boss': {
        name: 'BOSS直聘',
        start: '#4facfe',
        end: '#00f2fe'
      },
      '51job': {
        name: '51Job',
        start: '#43e97b',
        end: '#38f9d7'
      }
    };

    // 只处理存在的平台
    const existingPlatforms = allPlatforms.filter(platform => rawData[platform]);

    existingPlatforms.forEach(platform => {
      const platformData = rawData[platform];
      const dataMap = new Map<string, number>();

      platformData.forEach((item: any[]) => {
        const dateStr = item[0].split('T')[0];
        dataMap.set(dateStr, item[1] || 0);
      });

      // 对齐数据到所有日期
      const alignedData: number[] = [];
      categories.forEach(date => {
        alignedData.push(dataMap.get(date) || 0);
      });

      seriesDataMap[platform] = alignedData;
    });

    await nextTick();
    renderChart(categories, seriesDataMap, existingPlatforms, platformConfig);

  } catch (err: any) {
    console.error("Failed to fetch training data:", err);
    error.value = err.message || "网络异常，请稍后重试";
  } finally {
    loading.value = false;
  }
};

// --- ECharts 渲染逻辑 ---
const renderChart = (
  categories: string[],
  seriesMap: Record<string, number[]>,
  platforms: string[],
  platformConfig: Record<string, { name: string; start: string; end: string }>
) => {
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

  // 构建 series 列表（按照 platforms 的顺序，索引越小越在底层）
  const seriesList = platforms.map((platform) => {
    const config = platformConfig[platform];

    return {
      name: config.name,
      type: 'line',
      stack: 'Total',
      smooth: true,
      lineStyle: {
        width: 0
      },
      showSymbol: false,
      areaStyle: {
        opacity: 0.85,
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: config.start },
          { offset: 1, color: config.end }
        ])
      },
      emphasis: {
        focus: 'series',
        areaStyle: {
          opacity: 1.0
        }
      },
      data: seriesMap[platform] || [],
      connectNulls: false
    };
  });

  // 计算 Y 轴的最大值
  const allValues = Object.values(seriesMap).flat();
  const maxValue = Math.max(...allValues, 0);
  const yAxisMax = Math.ceil(maxValue * 1.1);

  const option = {
    backgroundColor: '#fff',
    title: {
      text: '岗位爬取总量趋势',
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

        let html = `<div style="font-weight:bold; margin-bottom:8px; font-size:13px;">
          ${params[0].axisValue}
          <span style="font-weight:normal; font-size:12px; opacity:0.8">
            (总计: ${total >= 10000 ? (total/10000).toFixed(2)+'w' : total.toLocaleString()})
          </span>
        </div>`;

        const sortedParams = [...params].sort((a, b) => b.value - a.value);

        sortedParams.forEach(p => {
          let valDisplay = p.value;
          if (p.value >= 10000) {
            valDisplay = (p.value / 10000).toFixed(2) + 'w';
          } else {
            valDisplay = p.value.toLocaleString();
          }

          html += `<div style="display:flex; justify-content:space-between; align-items:center; min-width:160px; margin-top:6px;">
            <span style="display:flex; align-items:center;">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color};margin-right:8px;"></span>
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
      bottom: 2,
      left: 'center',
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
          title: '保存为图片',
          pixelRatio: 2,
          iconStyle: { borderColor: '#999' }
        },
        magicType: {
          title: { line: '折线图', bar: '柱状图' },
          type: ['line', 'bar']
        }
      },
      right: 8,
      top: 8,
      iconSize: 14
    },
    grid: {
      left: '8%',
      right: '5%',
      bottom: '12%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: categories.map(date => date.substring(5)),
      axisLine: {
        lineStyle: { color: '#e0e0e0', width: 1 }
      },
      axisTick: { show: false },
      axisLabel: {
        color: '#888',
        fontSize: 10,
        interval: 'auto',
        margin: 10,
        rotate: categories.length > 7 ? 30 : 0
      }
    },
    yAxis: {
      type: 'value',
      name: '岗位数量',
      nameTextStyle: {
        fontSize: 10,
        color: '#888'
      },
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
          if (value >= 1000) return (value / 1000).toFixed(0) + 'k';
          return value.toString();
        }
      },
      min: 0,
      max: yAxisMax
    },
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
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
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