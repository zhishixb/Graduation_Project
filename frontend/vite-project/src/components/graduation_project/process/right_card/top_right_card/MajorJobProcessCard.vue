<template>
  <div class="major-job-process-card-container" id="major-job-process-card-container">
    <!-- 头部 -->
    <div class="major-job-process-card-header">
      <div class="major-job-process-card-title">微调数据清洗</div>
      <n-button
        circle
        size="small"
        :loading="isLoadingData"
        :disabled="isRunning"
        @click="openDrawer"
        class="major-job-process-action-btn"
        type="info"
        strong
        secondary
      >
        <template #icon>
          <n-icon><AddCircleOutline /></n-icon>
        </template>
      </n-button>
    </div>

    <!-- 主体占位 -->
    <div class="start-card-right">
      <div v-if="contentText && !selectedMajorName" class="status-text" :style="{ color: contentColor }">
        {{ contentText }}
      </div>
    </div>

    <n-drawer
      v-model:show="isDrawerOpen"
      width="100%"
      placement="left"
      :mask="false"
      :trap-focus="false"
      :block-scroll="false"
      to="#major-job-process-card-container"
      class="local-drawer"
    >
      <n-drawer-content closable style="height: 100%; display: flex; flex-direction: column;">
        <n-cascader
          v-model:value="selectedMajorName"
          :options="processedData.options"
          :disabled="isLoadingData || isRunning || !processedData.ready"
          placeholder="选专业"
          size="small"
          clearable
          filterable
          show-path
          :emit-path="false"
          class="major-cascader"
          @update:value="handleMajorChange"
          :to="'body'"
          style="width: 100%;"
        />

        <!-- 可选：增加一些提示文字 -->
        <div style="font-size: 12px; color: #999; margin-top: 8px; text-align: center;">
          请选择专业以开始
        </div>

      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
// ... (脚本部分保持不变，逻辑与之前一致) ...
import { useMessage } from 'naive-ui'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

import {AddCircleOutline} from '@vicons/ionicons5'

import {getMajorsList} from "@/apis/spider.ts";

function isRawDataMap(obj: unknown): obj is RawDataMap {
  if (typeof obj !== 'object' || obj === null) return false;
  for (const key in obj) {
    const secondLevel = obj[key];
    if (typeof secondLevel !== 'object' || secondLevel === null) return false;
    for (const subKey in secondLevel) {
      const thirdLevel = secondLevel[subKey];
      if (typeof thirdLevel !== 'object' || thirdLevel === null) return false;
      for (const finalKey in thirdLevel) {
        const detail = thirdLevel[finalKey];
        if (typeof detail !== 'object' || detail === null || !('state' in detail)) return false;
      }
    }
  }
  return true;
}

const message = useMessage()
const selectedMajorName = ref<string | null>(null)
const isLoadingData = ref(false)
const isRunning = ref(false)
const contentText = ref('等待选择...')
const contentColor = ref('#969696')
const rawCascaderData = ref<RawDataMap | null>(null)
const isDrawerOpen = ref(false)

interface MajorDetail { state: number; [key: string]: any }
interface RawDataMap { [category: string]: { [secondary: string]: { [majorName: string]: MajorDetail } } }
interface CascaderOption { label: string; value: string; disabled?: boolean; children?: CascaderOption[]; _pathInfo?: { category: string; secondary: string } }
interface ProcessedData { ready: boolean; options: CascaderOption[]; pathMap: Map<string, { category: string; secondary: string }>; }

const processedData = computed<ProcessedData>(() => {
  if (!rawCascaderData.value)
    return { ready: false, options: [], pathMap: new Map() }
  const options: CascaderOption[] = []
  const pathMap = new Map<string, { category: string; secondary: string }>()
  for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
    if (typeof secondaries !== 'object' || secondaries === null)
      continue
    const categoryNode: CascaderOption = {
      label: category, value: category, children: []
    }
    for (const [secondary, majors] of Object.entries(secondaries)) {
      if (typeof majors !== 'object' || majors === null) continue
      const secondaryNode: CascaderOption = {
        label: secondary,
        value: secondary,
        children: []
      }
      let hasValidMajor = false
      for (const [majorName, detail] of Object.entries(majors)) {
        if (!detail || typeof detail.state !== 'number')
          continue
        const majorNode: CascaderOption = {
          label: majorName, value: majorName,
          disabled: detail.state === 0 || detail.state === 1,
          _pathInfo: { category, secondary }
        }
        secondaryNode.children!.push(majorNode)
        pathMap.set(majorName, { category, secondary })
        hasValidMajor = true
      }
      if (hasValidMajor)
        categoryNode.children!.push(secondaryNode)
    }
    if (categoryNode.children!.length > 0)
      options.push(categoryNode)
  }
  return { ready: true, options, pathMap }
})

const fetchCountJobs = async () => {
  try {
    const res = await getMajorsList()

    if (res && typeof res === 'object' && 'success' in res) {
      if (res.success && res.data && isRawDataMap(res.data)) {
        rawCascaderData.value = res.data
        contentText.value = '数据就绪，请选择专业'
        contentColor.value = '#37ddbf'
        console.log("✅ 数据加载成功，条目数:", Object.keys(res.data).length)
      } else {
        rawCascaderData.value = {}
        contentText.value = res.message || '数据格式不正确'
        contentColor.value = '#ff4d4f'
        console.warn("⚠️ 数据格式不正确:", res.data)
      }
    } else {
      rawCascaderData.value = {}
      contentText.value = 'API响应异常'
      contentColor.value = '#ff4d4f'
    }
  } catch (e) {
    console.error('❌ 请求失败:', e)
    message.error('加载数据失败')
    rawCascaderData.value = {}
    contentText.value = '加载失败'
    contentColor.value = '#ff4d4f'
  } finally {
    isLoadingData.value = false
  }
}

const handleError = (msg: string, isManual: boolean) => {
  rawCascaderData.value = {};
  contentText.value = msg;
  contentColor.value = '#ff4d4f';
  if (isManual)
    message.error(msg)
}
const openDrawer = () => {
  if (!isRunning.value)
    isDrawerOpen.value = true;
  else
    message.warning('运行中不可用')
}

const handleMajorChange = (value: string | null, path: any[]) => {
  selectedMajorName.value = value
  if (value && path && path.length >= 3) {
     // 简单处理路径显示
     const fullPath = path.map(p => p.label).join(' - ')
     contentText.value = fullPath
     contentColor.value = '#6cb1ff'
  } else if (!value) {
    contentText.value = '等待选择...'; contentColor.value = '#969696'
  }
}
onMounted(() => fetchCountJobs(false))
onBeforeUnmount(() => { if (retryTimer) clearTimeout(retryTimer) })
</script>

<style scoped>
.major-job-process-card-container {
  width: 160px;
  height: 150px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background-color: #fefefe;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  position: relative;
  overflow: hidden; /* 必须保留，用于裁剪抽屉 */
}

.major-job-process-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  z-index: 1;
}

.major-job-process-card-title {
  font-weight: bold;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 110px;
}

.major-job-process-action-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  z-index: 1;
}

.start-card-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.status-text {
  font-size: 11px;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* --- 关键 CSS：修复局部抽屉样式 --- */

/* 1. 强制抽屉绝对定位并填满父容器 */
:deep(.local-drawer .n-drawer) {
  position: absolute !important;
  top: 0;
  left: 0;
  width: 100% !important;
  height: 100% !important;
  box-shadow: none; /* 内部不需要大阴影 */
  background-color: #fff;
}

/* 2. 确保内容区域占满剩余空间 */
:deep(.local-drawer .n-drawer-content) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.local-drawer .n-drawer-content__body) {
  padding: 12px;
  flex: 1;
  overflow-y: auto; /* 允许内部滚动 */
}

:deep(.local-drawer .n-drawer-header) {
  padding: 8px 12px;
  min-height: auto;
  border-bottom: 1px solid #f0f0f0;
}

.major-cascader {
  width: 100%;
}
</style>