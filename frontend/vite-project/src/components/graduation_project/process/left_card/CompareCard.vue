<template>
  <!-- 外层容器：严格锁定 620x400 -->
  <div class="compare-card-wrapper">

    <!-- 左侧：图表区域 -->
    <div class="chart-section">
      <n-tabs
        type="line"
        animated
        v-model:value="currentChartType"
        @update:value="handleTabChange"
        class="chart-tabs"
        size="small"
      >
        <n-tab-pane name="polar" tab="极坐标对比" />
        <n-tab-pane name="bar" tab="柱状统计" />
        <n-tab-pane name="line" tab="趋势折线" />
        <n-tab-pane name="pie" tab="占比分布" />
      </n-tabs>

      <div ref="chartRef" class="chart-box"></div>
    </div>

    <!-- 右侧：交互面板 -->
    <div class="info-section">
      <ModelCompareCard
        :model-options="modelOptions"
        :major-raw-data="rawMajorData"
        :position-raw-data="rawPositionData"
        @update:data="handleRealDataUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { NTabs, NTabPane } from 'naive-ui';
import * as echarts from 'echarts';
import ModelCompareCard from "./compare/ModelCompareCard.vue";
import { getModelList } from "@/apis/model";
import { getMajorsList, getJobList } from "@/apis/spider";

// --- 1. 状态定义 ---
const currentChartType = ref('polar');
const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// 基础配置数据
const rawModelList = ref<string[]>([]);
const rawMajorData = ref<any>(null);
const rawPositionData = ref<any>(null);

// 计算属性：格式化下拉框选项
const modelOptions = computed(() => {
  return rawModelList.value.map(name => ({ label: name, value: name }));
});

// 【新增】存储最新的实时数据，以便切换 Tab 时使用
let latestRealData: any = null;

// --- 2. 数据中心 (静态配置) ---
interface ChartMeta {
  title: string;
  scenario: string;
  getOption: () => any;
}

const chartConfig: Record<string, ChartMeta> = {
  polar: {
    title: '双模型匹配度对比',
    scenario: '通过双半圆极坐标，直观对比模型在选定职位上的表现差异。',
    // 注意：这里的 data 是默认占位符，会被实时数据覆盖
    getOption: () => ({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}'
      },
      angleAxis: [
        {
          type: 'category',
          polarIndex: 0,
          startAngle: 90,
          endAngle: 0,
          data: ['准确率', '召回率', 'F1 分数'], // 默认值
          axisLabel: { color: '#5470c6', fontWeight: 'bold', distance: 25, fontSize: 12 }
        },
        {
          type: 'category',
          polarIndex: 1,
          startAngle: -90,
          endAngle: -180,
          data: ['准确率', '召回率', 'F1 分数'], // 默认值
          axisLabel: { color: '#91cc75', fontWeight: 'bold', distance: 25, fontSize: 12 }
        }
      ],
      radiusAxis: [
        { polarIndex: 0, max: 1, min: 0, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#eee' } } },
        { polarIndex: 1, max: 1, min: 0, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#eee' } } }
      ],
      polar: [{}, {}],
      series: [
        {
          name: 'Model A',
          type: 'bar',
          polarIndex: 0,
          data: [0.85, 0.70, 0.76], // 默认值
          coordinateSystem: 'polar',
          itemStyle: { color: '#5470c6', borderRadius: [6, 6, 0, 0] },
          label: { show: true, position: 'outside', formatter: '{c}', color: '#5470c6', fontSize: 11 }
        },
        {
          name: 'Model B',
          type: 'bar',
          polarIndex: 1,
          data: [0.88, 0.82, 0.84], // 默认值
          coordinateSystem: 'polar',
          itemStyle: { color: '#91cc75', borderRadius: [6, 6, 0, 0] },
          label: { show: true, position: 'outside', formatter: '{c}', color: '#91cc75', fontSize: 11 }
        }
      ]
    })
  },
  bar: {
    title: '月度流量统计',
    scenario: '展示周一至周五的服务器流量峰值。',
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
    scenario: '追踪版本迭代中的响应时间变化。',
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
    scenario: '分析当前活跃用户的访问渠道占比。',
    getOption: () => ({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { show: false },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
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

// --- 3. 核心逻辑：数据转换与图表更新 ---

/**
 * 将后端返回的嵌套数据转换为 ECharts Polar 格式
 * 输入: { "modelA": { "job1": 0.5, "job2": 0.6 }, "modelB": { ... } }
 * 输出: { categories: ["job1", "job2"], series: [ {name: "modelA", data: [0.5, 0.6]}, ... ] }
 */
const transformPolarData = (rawData: any) => {
  if (!rawData) return null;

  const modelNames = Object.keys(rawData);
  if (modelNames.length < 1) return null;

  // 获取所有职位 (假设所有模型下的职位集合一致，取第一个模型的 key)
  const firstModel = modelNames[0];
  const jobs = Object.keys(rawData[firstModel]);

  // 构建 Series 数据
  const seriesData = modelNames.map((modelName, index) => {
    const modelData = rawData[modelName];
    // 按照 jobs 的顺序提取分数
    const values = jobs.map(job => modelData[job] || 0);

    return {
      name: modelName,
      type: 'bar',
      polarIndex: index % 2, // 只有两个极坐标区，轮流分配 (0 或 1)
      data: values,
      coordinateSystem: 'polar',
      itemStyle: {
        color: index === 0 ? '#5470c6' : '#91cc75', // 固定颜色方案
        borderRadius: [6, 6, 0, 0]
      },
      label: {
        show: true,
        position: 'outside',
        formatter: '{c}',
        color: index === 0 ? '#5470c6' : '#91cc75',
        fontSize: 11
      }
    };
  });

  return {
    categories: jobs,
    series: seriesData
  };
};

/**
 * 更新极坐标图表
 */
const updatePolarChart = (rawData: any) => {
  if (!chartInstance) return;

  const transformed = transformPolarData(rawData);
  if (!transformed) {
    console.warn("数据格式无法转换");
    return;
  }

  // 动态构建 Option
  const newOption = {
    angleAxis: [
      {
        type: 'category',
        polarIndex: 0,
        startAngle: 90,
        endAngle: 0,
        data: transformed.categories, // 【动态】使用真实职位名
        axisLabel: { color: '#5470c6', fontWeight: 'bold', distance: 25, fontSize: 12 }
      },
      {
        type: 'category',
        polarIndex: 1,
        startAngle: -90,
        endAngle: -180,
        data: transformed.categories, // 【动态】使用真实职位名
        axisLabel: { color: '#91cc75', fontWeight: 'bold', distance: 25, fontSize: 12 }
      }
    ],
    // radiusAxis 保持不变 (0-1)
    radiusAxis: [
      { polarIndex: 0, max: 1, min: 0, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#eee' } } },
      { polarIndex: 1, max: 1, min: 0, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#eee' } } }
    ],
    polar: [{}, {}],
    series: transformed.series // 【动态】使用真实数据
  };

  // 使用 notMerge: false 以保留 tooltip 等全局配置，仅更新坐标轴和系列
  chartInstance.setOption(newOption, { notMerge: false });
};

// --- 4. 事件处理 ---

const handleRealDataUpdate = (data: any) => {
  console.log("收到右侧子组件传来的真实数据:", data);

  // 数据结构可能是 { success: true, data: { success: true, data: { ... } } }
  // 需要层层解包找到真正的 payload
  let payload = data;
  if (data?.data?.data) {
    payload = data.data.data;
  } else if (data?.data) {
    payload = data.data;
  }

  if (!payload || typeof payload !== 'object') {
    console.warn("无效的数据负载");
    return;
  }

  latestRealData = payload; // 缓存数据

  // 如果当前正在看极坐标图，立即更新
  if (currentChartType.value === 'polar') {
    updatePolarChart(payload);
  } else {
    console.log(`当前视图为 ${currentChartType.value}，暂不更新极坐标，待切换时渲染。`);
  }
};

const handleTabChange = (type: string) => {
  if (!chartInstance) return;

  chartInstance.clear();

  // 特殊逻辑：如果是切换到 polar，且有新数据，则使用新数据渲染
  if (type === 'polar' && latestRealData) {
    // 先加载基础配置模板
    const baseOption = chartConfig['polar'].getOption();
    chartInstance.setOption(baseOption, { notMerge: true });
    // 再叠加真实数据
    updatePolarChart(latestRealData);
  } else {
    // 其他图表或无新数据时，使用静态配置
    const option = chartConfig[type].getOption();
    chartInstance.setOption(option, { notMerge: true });
  }
};

// 加载基础列表数据
const loadBaseData = async () => {
  try {
    const [mRes, majRes, posRes] = await Promise.all([
      getModelList(),
      getMajorsList(),
      getJobList()
    ]);
    rawModelList.value = mRes.data?.data || mRes.data || [];
    rawMajorData.value = majRes.data;
    rawPositionData.value = posRes.data;
  } catch (e) {
    console.error("基础数据加载失败", e);
  }
};

// --- 5. 生命周期 ---
onMounted(() => {
  loadBaseData();

  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    // 初始渲染
    chartInstance.setOption(chartConfig['polar'].getOption());

    window.addEventListener('resize', handleResize);
    const resizeObserver = new ResizeObserver(() => chartInstance?.resize());
    resizeObserver.observe(chartRef.value);
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
/* 样式保持不变 */
.compare-card-wrapper {
  width: 620px;
  height: 400px;
  max-width: 620px;
  max-height: 400px;
  display: flex;
  gap: 16px;
  padding: 16px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.chart-section {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.chart-tabs {
  margin-bottom: 8px;
  flex-shrink: 0;
}
:deep(.n-tabs) {
  --n-tab-font-size: 12px;
  --n-tab-height: 30px;
}

.chart-box {
  flex: 1;
  width: 100%;
  min-height: 0;
}

.info-section {
  width: 240px;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.config-component-root {
  width: 100%;
  height: 100%;
}
</style>