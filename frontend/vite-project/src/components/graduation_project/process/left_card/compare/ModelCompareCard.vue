<!-- src/components/ModelCompareConfig.vue -->
<template>
  <n-card
    title="数据配置"
    size="small"
    class="info-card"
    :bordered="false"
    id="drawer-target"
  >
    <template #header-extra>
      <n-tag type="primary" size="small" round class="config-tag">
        CONFIG
      </n-tag>
    </template>

    <div class="card-content">
      <div class="section-title">
        <span class="title-icon">⚙️</span> 配置模型、专业及职位
      </div>

      <!-- 表单区域 (保持不变) -->
      <div class="input-group">
        <n-select
          v-model:value="selectedModels"
          placeholder="请选择模型 (最多 2 个)..."
          :options="modelOptions"
          multiple
          clearable
          @update:value="handleModelLimit"
          class="custom-input"
          :disabled="localLoading"
          size="small"
        />
      </div>

      <div class="input-group">
        <n-cascader
          v-model:value="selectedMajors"
          v-model:show="majorCascaderShow"
          :options="processedMajorOptions"
          placeholder="请选择专业 (限 1 个)..."
          size="small"
          clearable
          filterable
          show-path
          multiple
          :max-tag-count="1"
          class="custom-input"
          :disabled="localLoading"
          @update:value="handleMajorLimit"
        />
      </div>

      <div class="input-group">
        <n-cascader
          v-model:value="selectedPositions"
          v-model:show="positionCascaderShow"
          :options="processedPositionOptions"
          placeholder="请选择职位 (最多 3 个)..."
          size="small"
          clearable
          filterable
          show-path
          multiple
          :max-tag-count="3"
          class="custom-input"
          :disabled="localLoading"
          @update:value="handlePositionLimit"
        />
      </div>

      <!-- 按钮组 -->
      <div class="action-group">
        <n-button
          type="info"
          secondary
          class="action-btn"
          @click="executeCompare"
          :loading="localLoading"
          :disabled="!isValid"
          block
        >
          <template #icon>
            <n-icon v-if="!localLoading"><PlayArrowIcon /></n-icon>
          </template>
          {{ localLoading ? '正在分析...' : '开始对比分析' }}
        </n-button>

        <n-button
          type="error"
          secondary
          class="clear-btn"
          @click="clearAllSelection"
          :disabled="!hasSelection"
          block
        >
          <template #icon>
            <n-icon><TrashIcon /></n-icon>
          </template>
          清空所有选择
        </n-button>
      </div>
    </div>

    <template #footer>
      <div class="card-footer">
        <span class="tip-icon">💡</span>
        <n-text depth="3" style="font-size: 11px; font-weight: 500;">配置完成后点击“开始对比分析”</n-text>
      </div>
    </template>
  </n-card>

  <!-- ✨ 结果分析抽屉 -->
  <n-drawer
    v-model:show="drawerVisible"
    placement="right"
    :width="'100%'"
    :mask="false"
    class="result-drawer"
    :trap-focus="false"
    :block-scroll="false"
    to="#drawer-target"
    style="padding: 0; margin: 0; overflow: hidden"
  >
    <n-drawer-content title="双模型匹配度对比" closable>

      <div v-if="localLoading && !compareResult" class="drawer-loading">
        <n-spin size="large" description="正在生成深度分析报告..." />
      </div>

      <div v-else-if="compareResult" class="drawer-content">

        <div class="chart-container">
          <div class="chart-legend">
            <div class="legend-item">
              <span class="dot" style="background-color: #5470c6;"></span>
              <span>{{ compareResult.model_a }} (基线)</span>
            </div>
            <div class="legend-item">
              <span class="dot" style="background-color: #91cc75;"></span>
              <span>{{ compareResult.model_b }} (新版)</span>
            </div>
          </div>
        </div>

        <n-divider style="margin: 16px 0;" />

        <!-- 2. 详细数据结论 -->
        <div class="analysis-section">
          <n-space vertical size="small">
            <n-alert type="info" title="综合评估">
              <template #icon>
                <n-icon><InfoIcon /></n-icon>
              </template>
              在 <strong>{{ compareResult.major }}</strong> 专业的 <strong>{{ compareResult.jobs}}</strong> 场景下：
              <br/>
              <span v-if="compareResult.score_b > compareResult.score_a">
                <strong>{{ compareResult.model_b }}</strong> 表现更优，综合得分高出 {{ (compareResult.score_b - compareResult.score_a).toFixed(1) }} 分。
              </span>
              <span v-else>
                <strong>{{ compareResult.model_a }}</strong> 表现更稳健，但在部分细分指标上 {{ compareResult.model_b }} 有追赶趋势。
              </span>
            </n-alert>

            <n-descriptions bordered :column="2" size="small">
              <n-descriptions-item label="对比模型 A">{{ compareResult.model_a }}</n-descriptions-item>
              <n-descriptions-item label="对比模型 B">{{ compareResult.model_b }}</n-descriptions-item>
              <n-descriptions-item label="目标专业">{{ compareResult.major }}</n-descriptions-item>
              <n-descriptions-item label="涉及职位">
                <n-space>
                  <n-tag v-for="job in compareResult.jobs" :key="job" size="tiny" type="info">{{ job }}</n-tag>
                </n-space>
              </n-descriptions-item>
            </n-descriptions>
          </n-space>
        </div>

        <!-- 3. 底部操作 -->
        <div class="drawer-footer">
          <n-button type="primary" block @click="exportReport">导出详细 PDF 报告</n-button>
        </div>
      </div>

    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue';
import * as echarts from 'echarts';
import {
  NCard, NTag, NText, NSelect, NCascader, NButton, NIcon,
  useMessage, NDrawer, NDrawerContent, NSpin, NAlert,
  NDescriptions, NDescriptionsItem, NDivider, NSpace
} from 'naive-ui';
import { PlayOutline, TrashOutline, AlertCircleOutline } from '@vicons/ionicons5';
import { compareModels, type ModelCompareParams } from "@/apis/model.ts";

const message = useMessage();
const PlayArrowIcon = PlayOutline;
const TrashIcon = TrashOutline;
const InfoIcon = AlertCircleOutline;

// ==========================================
// 1. 类型定义
// ==========================================
interface ModelOption { label: string; value: string; }
interface RawDataMap { [category: string]: { [secondary: string]: { [itemName: string]: any; }; }; }
interface CascaderOption {
  label: string; value: string; disabled?: boolean; children?: CascaderOption[];
  _fullPath?: { category: string; secondary: string; item: string; id?: string };
}

// 模拟结果数据结构 (根据实际 API 调整，这里假设 API 返回了 score_a, score_b 等)
interface CompareResultData {
  model_a: string;
  model_b: string;
  major: string;
  jobs: string[];
  score_a?: number; // 假设 API 返回了总分
  score_b?: number;
  metrics?: {
    // 假设 API 返回了具体指标，如果没有，下面逻辑会生成模拟数据
    model_a: { accuracy: number; recall: number; f1: number };
    model_b: { accuracy: number; recall: number; f1: number };
  };
  [key: string]: any;
}

// ==========================================
// 2. Props & Emits
// ==========================================
const { modelOptions, majorRawData, positionRawData } = defineProps<{
  modelOptions: ModelOption[];
  majorRawData: RawDataMap | null;
  positionRawData: RawDataMap | null;
}>();

const emit = defineEmits<{ 'update:data': [data: any] }>();

// ==========================================
// 3. 内部状态
// ==========================================
const selectedModels = ref<string[]>([]);
const selectedMajors = ref<string[]>([]);
const selectedPositions = ref<string[]>([]);
const localLoading = ref(false);
const majorCascaderShow = ref(false);
const positionCascaderShow = ref(false);

// 抽屉与图表状态
const drawerVisible = ref(false);
const compareResult = ref<CompareResultData | null>(null);
const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// ==========================================
// 4. 数据处理逻辑 (保持不变)
// ==========================================
function isRawDataMap(obj: unknown): obj is RawDataMap {
  if (typeof obj !== 'object' || obj === null) return false;
  for (const key in obj) {
    const secondLevel = (obj as any)[key];
    if (typeof secondLevel !== 'object' || secondLevel === null) return false;
    for (const subKey in secondLevel) {
      const thirdLevel = (secondLevel as any)[subKey];
      if (typeof thirdLevel !== 'object' || thirdLevel === null) return false;
    }
  }
  return true;
}

const convertToCascaderOptions = (rawData: RawDataMap | null): CascaderOption[] => {
  if (!rawData || !isRawDataMap(rawData)) return [];
  const options: CascaderOption[] = [];
  Object.entries(rawData).forEach(([category, secondaries]) => {
    const categoryNode: CascaderOption = { label: category, value: category, children: [] };
    Object.entries(secondaries).forEach(([secondary, items]) => {
      const secondaryNode: CascaderOption = { label: secondary, value: secondary, children: [] };
      Object.entries(items).forEach(([itemName, detail]) => {
        secondaryNode.children!.push({
          label: itemName, value: itemName,
          _fullPath: { category, secondary, item: itemName, id: detail.id }
        });
      });
      if (secondaryNode.children!.length > 0) categoryNode.children!.push(secondaryNode);
    });
    if (categoryNode.children!.length > 0) options.push(categoryNode);
  });
  return options;
};

const processedMajorOptions = computed(() => convertToCascaderOptions(majorRawData));
const processedPositionOptions = computed(() => convertToCascaderOptions(positionRawData));

const isValid = computed(() =>
  selectedModels.value.length >= 2 && selectedMajors.value.length >= 1 && selectedPositions.value.length >= 1
);
const hasSelection = computed(() =>
  selectedModels.value.length > 0 || selectedMajors.value.length > 0 || selectedPositions.value.length > 0
);

// ==========================================
// 5. 图表渲染逻辑 (核心修改)
// ==========================================
const renderPolarChart = () => {
  if (!chartRef.value || !compareResult.value) return;

  // 初始化或获取实例
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  // 获取数据 (如果 API 没返回具体指标，这里生成模拟数据用于演示)
  const dataA = compareResult.value.metrics?.model_a || { accuracy: 85, recall: 70, f1: 76 };
  const dataB = compareResult.value.metrics?.model_b || { accuracy: 88, recall: 82, f1: 84 };

  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    angleAxis: [
      {
        type: 'category',
        polarIndex: 0,
        startAngle: 90,
        endAngle: 0, // 左半圆
        data: ['准确率', '召回率', 'F1 分数'],
        axisLabel: { color: '#5470c6', fontWeight: 'bold', distance: 25, fontSize: 12 }
      },
      {
        type: 'category',
        polarIndex: 1,
        startAngle: -90,
        endAngle: -180, // 右半圆
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
        name: compareResult.value.model_a,
        type: 'bar',
        polarIndex: 0,
        data: [dataA.accuracy, dataA.recall, dataA.f1],
        coordinateSystem: 'polar',
        itemStyle: { color: '#5470c6', borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'outside', formatter: '{c}', color: '#5470c6', fontSize: 11 }
      },
      {
        name: compareResult.value.model_b,
        type: 'bar',
        polarIndex: 1,
        data: [dataB.accuracy, dataB.recall, dataB.f1],
        coordinateSystem: 'polar',
        itemStyle: { color: '#91cc75', borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'outside', formatter: '{c}', color: '#91cc75', fontSize: 11 }
      }
    ]
  };

  chartInstance.setOption(option, { notMerge: true });

  // 确保尺寸正确
  nextTick(() => {
    chartInstance?.resize();
  });
};

// 监听抽屉打开，触发图表渲染
watch(drawerVisible, (newVal) => {
  if (newVal && compareResult.value) {
    nextTick(() => {
      renderPolarChart();
    });
  }
});

// 窗口大小变化时重绘
window.addEventListener('resize', () => chartInstance?.resize());

// ==========================================
// 6. 交互逻辑
// ==========================================
const handleModelLimit = (v: string[]) => selectedModels.value = v.length > 2 ? v.slice(0, 2) : v;

const handleMajorLimit = (v: string[]) => {
  if(v.length > 1) { selectedMajors.value = v.slice(0,1); setTimeout(()=>majorCascaderShow.value=false, 150); }
  else { selectedMajors.value = v; if(v.length) setTimeout(()=>majorCascaderShow.value=false, 150); }
};

const handlePositionLimit = (v: string[]) => {
  if(v.length > 3) { selectedPositions.value = v.slice(0,3); setTimeout(()=>positionCascaderShow.value=false, 150); }
  else { selectedPositions.value = v; if(v.length>=3) setTimeout(()=>positionCascaderShow.value=false, 150); }
};

const clearAllSelection = () => {
  selectedModels.value = []; selectedMajors.value = []; selectedPositions.value = [];
  majorCascaderShow.value = false; positionCascaderShow.value = false;
  drawerVisible.value = false;
  compareResult.value = null;
  chartInstance?.dispose();
  chartInstance = null;
  emit('update:data', null);
  message.success("已清空所有配置");
};

const executeCompare = async () => {
  if (!isValid.value) {
    message.warning("请完善所有配置项 (需 2 模型 + 1 专业 + 1 职位)");
    return;
  }

  localLoading.value = true;
  try {
    const params: ModelCompareParams = {
      model_a: selectedModels.value[0],
      model_b: selectedModels.value[1],
      major: selectedMajors.value[0],
      jobs: [...selectedPositions.value]
    };

    const res = await compareModels(params);

    if (res.success && res.data?.data) {
      message.success("对比完成！");

      // 保存结果
      compareResult.value = res.data;

      // 打开抽屉 (watch 会自动触发图表渲染)
      drawerVisible.value = true;

      emit('update:data', res.data.data);
      console.log('API 返回数据:', res.data);
    } else {
      message.error(res.message || "对比失败");
      emit('update:data', null);
    }
  } catch (error) {
    console.error(error);
    message.error("网络请求失败");
    emit('update:data', null);
  } finally {
    localLoading.value = false;
  }
};

const exportReport = () => {
  message.info("正在生成 PDF 报告... (功能开发中)");
};
</script>

<style scoped>
.info-card {
  height: 100%; display: flex; flex-direction: column; background: #fff;
  border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
  border: 1px solid #f0f0f0 !important; position: relative; z-index: 1;
}
.card-content { flex: 1; display: flex; flex-direction: column; gap: 12px; padding: 12px 8px; overflow-y: auto; }
.section-title { font-size: 13px; font-weight: 700; color: #333; display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 4px; }
.input-group { position: relative; flex-shrink: 0; }
.custom-input :deep(.n-base-selection) { border: 1px solid #e0e0e0 !important; background-color: #fafafa !important; }
.action-group { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; flex-shrink: 0; }
.action-btn { height: 36px; font-size: 14px; font-weight: 600; border-radius: 8px !important; }
.clear-btn { height: 36px; font-size: 13px; font-weight: 500; border-radius: 8px !important; }
.card-footer { border-top: 1px solid #f3f4f6; padding-top: 8px; margin-top: auto; display: flex; align-items: center; justify-content: center; gap: 6px; background: #fafafa; border-radius: 0 0 8px 8px; flex-shrink: 0; }

/* ✨ 新增：抽屉内部样式 */
.drawer-loading {
  display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px;
}

.drawer-content {
  padding: 0px;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow-y: auto;

}

.drawer-content::-webkit-scrollbar {
width: 1px; /* 设置滚动条宽度 */
}

/* 图表容器 */
.chart-container {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.polar-chart-box {
  width: 100%;
  height: 260px; /* 固定高度确保极坐标显示完美 */
}

.chart-legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  font-size: 12px;
  color: #666;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.chart-desc {
  margin-top: 12px;
  font-size: 12px;
  color: #999;
  text-align: center;
  line-height: 1.5;
}

.analysis-section {
  flex: 1;
}

.drawer-footer {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>