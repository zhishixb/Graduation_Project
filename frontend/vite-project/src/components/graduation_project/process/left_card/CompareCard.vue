<template>
  <!-- 外层容器 -->
  <div class="compare-card-wrapper">

    <!-- 左侧：图表 + 切换器 -->
    <div class="chart-section">
      <!-- Naive UI Tabs 切换器 -->
      <n-tabs
        type="line"
        animated
        v-model:value="currentChartType"
        @update:value="handleTabChange"
        class="chart-tabs"
      >
        <n-tab-pane name="polar" tab="极坐标对比" />
        <n-tab-pane name="bar" tab="柱状统计" />
        <n-tab-pane name="line" tab="趋势折线" />
        <n-tab-pane name="pie" tab="占比分布" />
      </n-tabs>

      <!-- 图表渲染容器 (所有 Tab 共用这一个 DOM 节点) -->
      <div ref="chartRef" class="chart-box"></div>

      <!-- 加载状态遮罩 -->
<!--      <n-spin :show="loading" size="small" class="loading-mask" />-->
    </div>

    <!-- 右侧：信息面板 (数据直接填充) -->
    <div class="info-section">
      <n-card
        title="数据洞察"
        size="small"
        hoverable
        class="info-card"
        :bordered="false"
      >
        <!-- 右上角标签 -->
        <template #header-extra>
          <n-tag :type="getStatusType(currentChartType)" size="small" round>
            {{ currentChartType.toUpperCase() }}
          </n-tag>
        </template>

        <!-- 动态内容区域 -->
        <div class="card-content">
          <h3 class="card-title">{{ currentConfig.title }}</h3>
          <p class="card-desc">{{ currentConfig.scenario }}</p>

          <!-- 图例列表 -->
          <div class="legend-list">
            <div class="legend-label">图例说明：</div>
            <div
              v-for="(item, index) in currentConfig.legends"
              :key="index"
              class="legend-item"
            >
              <span class="dot" :style="{ backgroundColor: item.color }"></span>
              <span class="text">{{ item.name }}</span>
              <!-- 如果是极坐标，显示额外提示 -->
              <span v-if="currentChartType === 'polar' && index === 0" class="hint">(基线)</span>
              <span v-if="currentChartType === 'polar' && index === 1" class="hint">(新版)</span>
            </div>
          </div>
        </div>

        <!-- 底部提示 -->
        <template #footer>
          <div class="card-footer">
            <n-text depth="3" style="font-size: 12px; line-height: 1.5;">
              💡 数据已直接嵌入组件。点击左上角标签可实时切换图表类型与右侧说明。
            </n-text>
          </div>
        </template>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { NTabs, NTabPane, NCard, NTag, NSpin, NText } from 'naive-ui';
import * as echarts from 'echarts';

// --- 1. 状态定义 ---
const currentChartType = ref('polar');
const loading = ref(false);
const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// --- 2. 数据中心 (直接填充的数据) ---
interface ChartMeta {
  title: string;
  scenario: string;
  legends: { name: string; color: string }[];
  getOption: () => any;
}

const chartConfig: Record<string, ChartMeta> = {
  polar: {
    title: '双模型匹配度对比',
    scenario: '通过双半圆极坐标，直观对比 S 系列（基线）与 T 系列（新版）在三个核心维度上的表现差异。',
    legends: [
      { name: 'S 系列 (基线)', color: '#5470c6' },
      { name: 'T 系列 (新版)', color: '#91cc75' }
    ],
    getOption: () => ({
      tooltip: { trigger: 'item', formatter: '{b}: {c}' },
      angleAxis: [
        {
          type: 'category',
          polarIndex: 0,
          startAngle: 90,
          endAngle: 0,
          data: ['准确率', '召回率', 'F1 分数'],
          axisLabel: { color: '#5470c6', fontWeight: 'bold', distance: 25, fontSize: 12 }
        },
        {
          type: 'category',
          polarIndex: 1,
          startAngle: -90,
          endAngle: -180,
          data: ['准确率', '召回率', 'F1 分数'],
          axisLabel: { color: '#91cc75', fontWeight: 'bold', distance: 25, fontSize: 12 }
        }
      ],
      radiusAxis: [
        { polarIndex: 0, max: 100, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#eee' } } },
        { polarIndex: 1, max: 100, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#eee' } } }
      ],
      polar: [{}, {}],
      series: [
        {
          name: 'S 系列',
          type: 'bar',
          polarIndex: 0,
          data: [85, 70, 76],
          coordinateSystem: 'polar',
          itemStyle: { color: '#5470c6', borderRadius: [6, 6, 0, 0] },
          label: { show: true, position: 'outside', formatter: '{c}', color: '#5470c6', fontSize: 11 }
        },
        {
          name: 'T 系列',
          type: 'bar',
          polarIndex: 1,
          data: [88, 82, 84],
          coordinateSystem: 'polar',
          itemStyle: { color: '#91cc75', borderRadius: [6, 6, 0, 0] },
          label: { show: true, position: 'outside', formatter: '{c}', color: '#91cc75', fontSize: 11 }
        }
      ]
    })
  },
  bar: {
    title: '月度流量统计',
    scenario: '展示周一至周五的服务器流量峰值，用于识别高负载时段以进行资源扩容。',
    legends: [{ name: '日均流量 (GB)', color: '#fac858' }],
    getOption: () => ({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五'], axisLine: { lineStyle: { color: '#999' } } },
      yAxis: { type: 'value', axisLine: { show: false }, splitLine: { lineStyle: { type: 'dashed' } } },
      series: [{
        name: '流量',
        type: 'bar',
        barWidth: '40%',
        data: [120, 200, 150, 80, 70],
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#fac858' }, { offset: 1, color: '#ee6666' }]) }
      }]
    })
  },
  line: {
    title: '性能趋势分析',
    scenario: '追踪 A/B/C/D/E 五个版本迭代中的响应时间变化，评估优化效果。',
    legends: [{ name: '平均响应时间 (ms)', color: '#ee6666' }],
    getOption: () => ({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false, data: ['Ver A', 'Ver B', 'Ver C', 'Ver D', 'Ver E'] },
      yAxis: { type: 'value', scale: true },
      series: [{
        name: '耗时',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: [45, 32, 28, 15, 12],
        itemStyle: { color: '#ee6666' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(238, 102, 102, 0.3)' },
            { offset: 1, color: 'rgba(238, 102, 102, 0.01)' }
          ])
        }
      }]
    })
  },
  pie: {
    title: '用户来源分布',
    scenario: '分析当前活跃用户的访问渠道占比，辅助制定市场推广策略。',
    legends: [
      { name: '搜索引擎', color: '#5470c6' },
      { name: '直接访问', color: '#91cc75' },
      { name: '邮件营销', color: '#fac858' },
      { name: '社交媒体', color: '#73c0de' }
    ],
    getOption: () => ({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { show: false }, // 隐藏默认图例，使用右侧自定义图例
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 20, fontWeight: 'bold' }
        },
        data: [
          { value: 1048, name: '搜索引擎', itemStyle: { color: '#5470c6' } },
          { value: 735, name: '直接访问', itemStyle: { color: '#91cc75' } },
          { value: 580, name: '邮件营销', itemStyle: { color: '#fac858' } },
          { value: 484, name: '社交媒体', itemStyle: { color: '#73c0de' } }
        ]
      }]
    })
  }
};

// --- 3. 计算属性与逻辑 ---

// 获取当前配置
const currentConfig = computed(() => chartConfig[currentChartType.value]);

// 切换处理
const handleTabChange = (type: string) => {
  if (!chartInstance) return;
  loading.value = true;

  // 模拟轻微延迟，增加切换质感
  setTimeout(() => {
    const option = chartConfig[type].getOption();
    // notMerge: true 关键：彻底清除旧坐标系，防止极坐标残留影响直角坐标
    chartInstance.setOption(option, { notMerge: true });
    loading.value = false;
  }, 200);
};

// 获取 Tag 颜色类型
const getStatusType = (type: string) => {
  const map: Record<string, any> = {
    polar: 'info',
    bar: 'warning',
    line: 'error',
    pie: 'success'
  };
  return map[type] || 'default';
};

// 生命周期
onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    // 初始化
    chartInstance.setOption(chartConfig['polar'].getOption());
    window.addEventListener('resize', handleResize);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
  chartInstance = null;
});

const handleResize = () => chartInstance?.resize();
</script>

<style scoped>
/* 布局容器 */
.compare-card-wrapper {
  width: 620px; /* 稍微宽一点以适应内容 */
  height: 400px;
  display: flex;
  gap: 20px;
  background-color: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 左侧区域 */
.chart-section {
  width: 360px;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
}

/* Tabs 样式覆盖 */
.chart-tabs {
  margin-bottom: 10px;
  flex-shrink: 0;
}
.chart-tabs :deep(.n-tabs-nav) {
  padding-left: 0;
}
.chart-tabs :deep(.n-tabs-panel-wrapper) {
  flex: 1;
  overflow: hidden; /* 防止溢出 */
}

/* 图表容器 */
.chart-box {
  width: 100%;
  height: 100%;
  min-height: 0; /* Flex 子元素关键 */
}

/* 加载遮罩 */
.loading-mask {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  pointer-events: none; /* 让点击穿透 */
}

/* 右侧区域 */
.info-section {
  width: 260px;
  height: 100%;
}

.info-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s;
}
.info-card:hover {
  transform: translateY(-2px);
}

/* 卡片内容排版 */
.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 0;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.card-desc {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  flex: 1; /* 让描述占据剩余空间，把图例挤下去 */
}

/* 图例列表 */
.legend-list {
  background: #f9fafb;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}

.legend-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
  font-weight: 500;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  color: #374151;
}
.legend-item:last-child {
  margin-bottom: 0;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
  box-shadow: 0 0 4px rgba(0,0,0,0.1);
}

.text {
  flex: 1;
}

.hint {
  font-size: 11px;
  color: #9ca3af;
  margin-left: 6px;
  background: #e5e7eb;
  padding: 1px 4px;
  border-radius: 4px;
}

/* 底部 */
.card-footer {
  border-top: 1px solid #f3f4f6;
  padding-top: 12px;
  margin-top: auto;
}
</style>