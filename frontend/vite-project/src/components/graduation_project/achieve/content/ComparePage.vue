<template>
  <div class="majordetail-content">
    <!-- 左侧专业信息面板 -->
    <div
      v-if="majorData"
      class="left-panel"
      :class="{ 'fade-in': showPanels }"
    >
      <MajorInfoPanel
        :major-name="store.getterMajorName()"
        :major-data="majorData"
      />
    </div>

    <!-- 右侧岗位详情面板 -->
    <div
      v-if="jobData"
      class="right-panel"
      :class="{ 'fade-in': showPanels }"
    >
      <JobInfoPanel
        :job-data="jobData"
      />
    </div>

    <!-- 右侧匹配分数区块 -->
    <div
      v-if="matchList && matchList.length > 0"
      class="extra-panel"
      :class="{ 'fade-in': showPanels }"
    >
      <div class="scroll-area">
        <h3 class="extra-title">
          <span>匹配度</span>
          <span
            v-if="averageValue !== null"
            class="level-inline"
            :class="{ 'level-low': averageValue < 0.717, 'level-high': averageValue >= 0.717 }"
          >
            <n-tooltip trigger="hover">
              <template #trigger>
                <span>{{ averageValue < 0.717 ? '较低' : '较高' }}</span>
              </template>
              <span>{{ averageValue < 0.717 ? '当前平均匹配度低于0.717，表明该岗位与专业的整体匹配程度偏低' : '当前平均匹配度达到或超过0.717，表明该岗位与专业整体匹配良好' }}</span>
            </n-tooltip>
          </span>
          <n-tooltip trigger="hover">
            <template #trigger>
              <InformationCircleOutline class="info-icon" />
            </template>
            <span>匹配度反映了当前岗位与专业的整体相似程度，数值越高表示越匹配。</span>
          </n-tooltip>
        </h3>

        <div class="score-row">
          <div class="score-item">
            <span class="score-label">最高匹配</span>
            <n-tooltip trigger="hover">
              <template #trigger>
                <span class="score-value">{{ highestMatch.score }}</span>
              </template>
              <span>由于岗位描述的差别，本值存在较大波动，只用作观赏，不存在实际意义</span>
            </n-tooltip>
          </div>
          <div class="score-item">
            <span class="score-label">平均匹配</span>
            <n-tooltip trigger="hover">
              <template #trigger>
                <span class="score-value">{{ averageMatch.score }}</span>
              </template>
              <span>反映整体匹配水平，判断匹配程度的核心标准</span>
            </n-tooltip>
          </div>
          <div class="score-item">
            <span class="score-label">最低匹配</span>
            <n-tooltip trigger="hover">
              <template #trigger>
                <span class="score-value">{{ lowestMatch.score }}</span>
              </template>
              <span>由于岗位描述的差别，本值存在较大波动，只用作观赏，不存在实际意义</span>
            </n-tooltip>
          </div>
        </div>

        <!-- 高精度匹配数据展示行 -->
        <div v-if="showPrecision && aggregatedScore" class="precision-row">
          <div class="precision-item">
            <span class="precision-label">高精度均值</span>
            <n-tooltip trigger="hover">
              <template #trigger>
                <span class="precision-value">{{ (aggregatedScore.mean * 100).toFixed(1) }}%</span>
              </template>
              <span>基于ColBERT语义模型的全局平均匹配度，更精确地反映整体匹配水平</span>
            </n-tooltip>
          </div>
          <div class="precision-item">
            <span class="precision-label">中位数</span>
            <n-tooltip trigger="hover">
              <template #trigger>
                <span class="precision-value">{{ (aggregatedScore.median * 100).toFixed(1) }}%</span>
              </template>
              <span>匹配度的中位数，用于评估匹配分布的集中趋势，不受极端值影响</span>
            </n-tooltip>
          </div>
        </div>
      </div>

      <div class="button-bar">
        <n-button size="tiny" quaternary @click="setView('map')">
          显示地图
        </n-button>
        <n-button size="tiny" quaternary @click="toggleKeywordsHeatmap">
          关键词热力图
        </n-button>
        <n-button size="tiny" quaternary @click="toggleRadar">
          领域雷达图
        </n-button>
        <n-button size="tiny" quaternary @click="openFullTokensDrawer">
          全词元热力图
        </n-button>
        <n-button size="tiny" quaternary @click="togglePrecision">
          {{ showPrecision ? '隐藏高精度' : '高精度匹配' }}
        </n-button>
      </div>
    </div>

    <!-- 地图动画区域（仅在地图模式时显示） -->
    <div
      v-show="activeView === 'map'"
      class="map-stage"
      :class="stageClass"
      @transitionend="onTransitionEnd"
    >
      <Map :data="provinceData" />
    </div>

    <!-- 关键词热力图 / 雷达图 共用容器 -->
    <div
      v-if="activeView === 'keywords' && currentSemanticPairs.length > 0"
      class="heatmap-stage"
    >
      <SemanticHeatmap
        :data="currentSemanticPairs"
        :key="'keyword-' + heatmapIndex"
      />
    </div>

    <div
      v-if="activeView === 'radar' && domainRadarData.length > 0"
      class="heatmap-stage"
    >
      <DomainRadar :data="domainRadarData" />
    </div>

    <!-- 全词元热力图抽屉 -->
    <n-drawer
      v-model:show="showFullTokenDrawer"
      :width="1280"
      placement="right"
    >
      <n-drawer-content title="全词元热力图" closable>
        <div v-if="currentFullTokenPair.length > 0" class="drawer-heatmap-container">
          <SemanticHeatmap :data="currentFullTokenPair" :width="1200" :height="640" />
        </div>
        <div v-else class="drawer-empty">暂无数据</div>
        <template #footer>
          <div class="drawer-footer">
            <n-button
              size="small"
              :disabled="fullTokenIndex <= 0"
              @click="prevFullTokenGroup"
            >
              上一组
            </n-button>
            <span class="group-indicator">
              {{ fullTokenIndex + 1 }} / {{ fullTokenHeatmapList.length }}
            </span>
            <n-button
              size="small"
              :disabled="fullTokenIndex >= fullTokenHeatmapList.length - 1"
              @click="nextFullTokenGroup"
            >
              下一组
            </n-button>
          </div>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NTooltip, NButton, NDrawer, NDrawerContent } from 'naive-ui'
import { InformationCircleOutline } from '@vicons/ionicons5'
import Map from '@/components/graduation_project/achieve/animated/Diagram.vue'
import JobInfoPanel from '@/components/graduation_project/achieve/page/job_detail/JobInfoPanel.vue'
import MajorInfoPanel from "@/components/graduation_project/achieve/page/major_detail/MajorInfoPanel.vue"
import SemanticHeatmap from "@/components/graduation_project/achieve/page/compare_page/SemanticHeatmap.vue"
import DomainRadar from "@/components/graduation_project/achieve/page/compare_page/DomainRadar.vue"
import { useDataStore } from '@/stores/achieve/dataStore.ts'
import { useBusinessStore } from '@/stores/achieve/business.ts'
import {
  getJobProvinceCount,
  getJobSkills,
  getMajorData,
  matchMajorJob,
  vectorMatchMajorJob,
  explainMatching,
  getDomainMatching,
  getMajorJobAggregatedScore
} from "@/apis/business.ts"

const store = useDataStore()
const businessStore = useBusinessStore()

type ViewMode = 'map' | 'keywords' | 'radar'

const stage = ref<'initial' | 'scaled' | 'moved'>('initial')
const showPanels = ref(false)
let scaledEnded = false

const jobData = ref()
const majorData = ref()
const matchList = ref<any[]>([])
const averageScore = ref<any>(null)
const provinceData = ref()

// 热力图状态
const heatmapList = ref<any[]>([])
const heatmapIndex = ref(0)
const fullTokenHeatmapList = ref<any[][]>([])
const fullTokenIndex = ref(0)
const activeView = ref<ViewMode>('map')
const showFullTokenDrawer = ref(false)

// 领域雷达图数据
const domainRadarData = ref<any[]>([])

// 高精度匹配数据及显示状态
const aggregatedScore = ref<{ max: number; mean: number; median: number } | null>(null)
const showPrecision = ref(false)

const stageClass = computed(() => {
  if (stage.value === 'moved') return 'scaled moved'
  if (stage.value === 'scaled') return 'scaled'
  return ''
})

const onTransitionEnd = (e: TransitionEvent) => {
  if (stage.value === 'scaled' && !scaledEnded && e.propertyName === 'transform') {
    scaledEnded = true
    stage.value = 'moved'
  }
  else if (stage.value === 'moved' && (e.propertyName === 'left' || e.propertyName === 'top')) {
    if (!showPanels.value) {
      showPanels.value = true
    }
  }
}

const highestMatch = computed(() => {
  if (!matchList.value || matchList.value.length === 0) return { index: null, score: '0%' }
  const item = matchList.value[0]
  return { index: item.index, score: (item.similarity * 100).toFixed(1) + '%' }
})

const lowestMatch = computed(() => {
  if (!matchList.value || matchList.value.length === 0) return { index: null, score: '0%' }
  const item = matchList.value[matchList.value.length - 1]
  return { index: item.index, score: (item.similarity * 100).toFixed(1) + '%' }
})

const averageMatch = computed(() => {
  const avg = averageScore.value
  if (avg == null) return { score: '0%' }
  const val = typeof avg === 'number' ? avg : (avg.similarity ?? 0)
  return { score: (val * 100).toFixed(1) + '%' }
})

const averageValue = computed<number | null>(() => {
  const avg = averageScore.value
  if (avg == null) return null
  return typeof avg === 'number' ? avg : (avg.similarity ?? null)
})

// 关键词热力图当前数据
const currentSemanticPairs = computed(() => {
  if (heatmapList.value.length === 0) return []
  const item = heatmapList.value[heatmapIndex.value]
  return item?.semantic_pairs || []
})

// 全词元热力图当前抽屉内展示的数据
const currentFullTokenPair = computed(() => {
  if (fullTokenHeatmapList.value.length === 0) return []
  return fullTokenHeatmapList.value[fullTokenIndex.value] || []
})

const setView = (mode: ViewMode) => {
  activeView.value = mode
}

const toggleKeywordsHeatmap = () => {
  if (activeView.value === 'keywords') {
    const total = heatmapList.value.length
    if (total <= 1) {
      setView('map')
    } else {
      heatmapIndex.value = (heatmapIndex.value + 1) % total
    }
  } else {
    heatmapIndex.value = 0
    setView('keywords')
  }
}

const toggleRadar = () => {
  if (activeView.value === 'radar') {
    setView('map')
  } else {
    setView('radar')
  }
}

const openFullTokensDrawer = () => {
  fullTokenIndex.value = 0
  showFullTokenDrawer.value = true
}

const prevFullTokenGroup = () => {
  if (fullTokenIndex.value > 0) {
    fullTokenIndex.value--
  }
}

const nextFullTokenGroup = () => {
  if (fullTokenIndex.value < fullTokenHeatmapList.value.length - 1) {
    fullTokenIndex.value++
  }
}

const togglePrecision = () => {
  showPrecision.value = !showPrecision.value
}

onMounted(async () => {
  const job = store.getterJobName()
  const res_1 = await getJobSkills(job)
  jobData.value = res_1.data

  if (!jobData.value?.function_name) {
    console.error('jobData 缺少 function_name')
    return
  }

  const major = store.getterMajorName()
  const res_2 = await getMajorData(major)
  majorData.value = res_2.data

  const function_name = jobData.value.function_name

  const functionNameList = [function_name]
  const res_3 = await getJobProvinceCount(functionNameList)
  provinceData.value = res_3.data

  const res_4 = await vectorMatchMajorJob(major, function_name)
  matchList.value = Array.isArray(res_4.data?.matches) ? res_4.data.matches : []

  const res_5 = await matchMajorJob(major, function_name)
  averageScore.value = res_5.data

  const res_6 = await explainMatching(major, function_name, 8, 5)
  if (res_6.success && Array.isArray(res_6.data?.explanations)) {
    heatmapList.value = res_6.data.explanations
    const allFullTokens: any[][] = []
    for (const exp of res_6.data.explanations) {
      if (exp.echarts_json) {
        try {
          const raw = typeof exp.echarts_json === 'string'
            ? JSON.parse(exp.echarts_json)
            : exp.echarts_json
          allFullTokens.push(businessStore.transformToSemanticPairs(raw))
        } catch (e) {
          console.warn('转换某组全词元数据失败', e)
          allFullTokens.push([])
        }
      } else {
        allFullTokens.push([])
      }
    }
    fullTokenHeatmapList.value = allFullTokens
  } else {
    heatmapList.value = []
    fullTokenHeatmapList.value = []
  }

  const res_7 = await getDomainMatching(major, function_name)
  if (res_7.success && Array.isArray(res_7.data?.domains)) {
    domainRadarData.value = res_7.data.domains
  }

  const res_8 = await getMajorJobAggregatedScore(major, function_name)
  if (res_8.success && res_8.data) {
    aggregatedScore.value = {
      max: res_8.data.max,
      mean: res_8.data.mean,
      median: res_8.data.median
    }
  }

  setTimeout(() => store.isLoading = false, 400)
  setTimeout(() => {
    requestAnimationFrame(() => {
      stage.value = 'scaled'
    })
  }, 400 + 800)
})
</script>

<style scoped>
.majordetail-content {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.left-panel,
.right-panel,
.extra-panel {
  opacity: 0;
  transition: opacity 0.6s ease;
}
.left-panel.fade-in,
.right-panel.fade-in,
.extra-panel.fade-in {
  opacity: 1;
  transition-delay: 0.8s;
}

.left-panel {
  position: absolute;
  left: 0;
  top: 0;
  width: 300px;
  height: 100%;
  overflow-y: auto;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 1;
  pointer-events: auto;
  box-sizing: border-box;
}

.left-panel::-webkit-scrollbar {
  width: 4px;
}
.left-panel::-webkit-scrollbar-track {
  background: transparent;
}
.left-panel::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 2px;
}

.right-panel {
  position: absolute;
  left: 300px;
  top: 0;
  width: 300px;
  height: 100%;
  overflow-y: auto;
  z-index: 1;
  pointer-events: auto;
  box-sizing: border-box;
}

.right-panel::-webkit-scrollbar {
  width: 4px;
}
.right-panel::-webkit-scrollbar-track {
  background: transparent;
}
.right-panel::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 2px;
}

.extra-panel {
  position: absolute;
  left: 600px;
  top: 0;
  width: 450px;
  height: 35%;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 1;
  pointer-events: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 16px 0 16px;
}

.scroll-area::-webkit-scrollbar {
  width: 4px;
}
.scroll-area::-webkit-scrollbar-track {
  background: transparent;
}
.scroll-area::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 2px;
}

.button-bar {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 16px 12px 16px;
  flex-shrink: 0;
}

.extra-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #3a4a5c;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  padding-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-inline {
  font-size: 12px;
  font-weight: 500;
  cursor: help;
  border-bottom: 1px dashed currentColor;
}

.level-low {
  color: #fa541c;
}

.level-high {
  color: #52c41a;
}

.info-icon {
  margin-left: auto;
  width: 16px;
  height: 16px;
  color: #aaa;
  cursor: help;
  transition: color 0.2s;
}
.info-icon:hover {
  color: #666;
}

.score-row {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 20px;
  margin-bottom: 16px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.score-label {
  color: #4b5563;
  font-weight: 500;
}

.score-value {
  color: #1677ff;
  font-weight: 700;
  font-size: 16px;
  cursor: help;
  border-bottom: 1px dashed #1677ff;
}

/* 地图动画 */
.map-stage {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  transition: transform 0.8s cubic-bezier(0.25, 0.8, 0.25, 1),
              left 0.8s cubic-bezier(0.25, 0.8, 0.25, 1),
              top 0.8s cubic-bezier(0.25, 0.8, 0.25, 1);
  z-index: 5;
  pointer-events: auto;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.map-stage.scaled {
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%) scale(0.6);
}

.map-stage.scaled.moved {
  left: 930px;
  top: 445px;
  transform: translate(-50%, -50%) scale(0.6);
}

/* 关键词热力图 / 雷达图 共用容器 */
.heatmap-stage {
  position: absolute;
  left: 820px;
  top: 445px;
  transform: translate(-50%, -50%) scale(0.9);
  width: 450px;
  height: 400px;
  z-index: 5;
  pointer-events: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 抽屉内热力图容器 */
.drawer-heatmap-container {
  width: 100%;
  height: calc(100vh - 180px);
  display: flex;
  justify-content: center;
  align-items: center;
}

.drawer-empty {
  text-align: center;
  color: #999;
  margin-top: 40px;
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.group-indicator {
  font-size: 13px;
  color: #666;
}

.precision-row {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 20px;
  margin-top: 8px;
  margin-bottom: 16px;
  padding: 8px 4px;
  background: rgba(22, 119, 255, 0.04);
  border-radius: 6px;
}

.precision-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.precision-label {
  color: #4b5563;
  font-weight: 500;
}

.precision-value {
  color: #1677ff;
  font-weight: 700;
  font-size: 15px;
  cursor: help;
  border-bottom: 1px dashed #1677ff;
}
</style>