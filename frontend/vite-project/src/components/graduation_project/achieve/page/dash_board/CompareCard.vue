<template>
  <div
    class="compare-wrapper"
    :class="{ 'fade-in': showReveal }"
  >
    <!-- 组件标题（左对齐） -->
    <div class="compare-title">专业岗位对比</div>

    <div class="compare-inner">
      <!-- 专业选择器 -->
      <NCascader
        v-model:value="majorValue"
        :options="majorOptions"
        placeholder="专业"
        class="compare-cascader"
        size="small"
        :show-path="false"
        clearable
      />

      <!-- 分隔线 -->
      <div class="divider"></div>

      <!-- 岗位选择器 -->
      <NCascader
        v-model:value="jobValue"
        :options="jobOptions"
        placeholder="岗位"
        class="compare-cascader"
        size="small"
        :show-path="false"
        clearable
      />

      <!-- 低调按钮 -->
      <button class="compare-btn" @click="handleCompare">
        <ReturnDownForward />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { NCascader } from 'naive-ui'
import { ReturnDownForward } from '@vicons/ionicons5'
import { getMajorStatus, getJobList } from '@/apis/business.ts'
import { useDataStore } from '@/stores/achieve/dataStore.ts'
import { useBusinessStore } from '@/stores/achieve/business.ts'

const store = useDataStore()
const businessStore = useBusinessStore()

const props = withDefaults(defineProps<{
  reveal?: boolean
}>(), {
  reveal: false
})

const majorValue = ref<string | null>(null)
const jobValue = ref<string | null>(null)
const majorOptions = ref<any[]>([])
const jobOptions = ref<any[]>([])

const emit = defineEmits<{
  compare: [payload: { major: string | null; job: string | null }]
}>()

const handleCompare = () => {
  const payload = {
    major: majorValue.value,
    job: jobValue.value
  }
  if (payload.major) store.selectMajorName(payload.major)
  if (payload.job) store.selectJobName(payload.job)
  store.isLoading = true
    setTimeout(() => {
    store.turnToPage("comparePage")
  }, 400);
  emit('compare', payload)
}

// --- 淡入逻辑 ---
const showReveal = ref(false)
let timer: ReturnType<typeof setTimeout> | null = null

watch(
  () => props.reveal,
  (val) => {
    if (timer) clearTimeout(timer)
    if (val) {
      timer = setTimeout(() => { showReveal.value = true }, 20)
    } else {
      showReveal.value = false
    }
  },
  { immediate: true }
)

onMounted(async () => {
  try {
    const [majorRes, jobRes] = await Promise.all([
      getMajorStatus(),
      getJobList()
    ])
    if (majorRes.success) {
      majorOptions.value = businessStore.buildMajorCascaderTree(majorRes.data)
    }
    if (jobRes.success) {
      jobOptions.value = businessStore.buildCascaderOptions(jobRes.data)
    }
  } catch (err) {
    console.error(err)
  }
})

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})
</script>

<style scoped>
/* 外层容器：宽度 300px，固定高度 */
.compare-wrapper {
  width: 300px;
  height: 80px;
  opacity: 0;
  transition: opacity 0.6s ease;
  box-sizing: border-box;
}

.compare-wrapper.fade-in {
  opacity: 1;
  transition-delay: 0.8s;
}

/* 标题：左对齐，小号灰色 */
.compare-title {
  font-size: 11px;
  font-weight: 500;
  color: #999;
  text-align: left;           /* 由 center 改为 left */
  padding-left: 4px;          /* 与下方选择器的左侧轻微对齐 */
  margin-bottom: 4px;
  line-height: 1.2;
  letter-spacing: 0.3px;
}

/* 内层 flex 水平排列 */
.compare-inner {
  display: flex;
  align-items: center;
  width: 100%;
  height: calc(100% - 20px);  /* 减去标题高度 + 间距 */
  padding: 0 6px 0 8px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  box-sizing: border-box;
}

.compare-cascader {
  flex: 1;
  min-width: 0;
}

.divider {
  width: 1px;
  height: 22px;
  background: #e0e0e0;
  flex-shrink: 0;
  margin: 0 6px;
}

.compare-btn {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border: none;
  background: #f0f0f0;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, box-shadow 0.2s;
  margin-left: 6px;
}

.compare-btn:hover {
  background: #e0e0e0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}

.compare-btn svg {
  width: 16px;
  height: 16px;
  fill: #555;
}

/* 级联选择器内部样式（保持不变） */
:deep(.compare-cascader),
:deep(.compare-cascader *) {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

:deep(.compare-cascader .n-base-selection),
:deep(.compare-cascader .n-base-selection__border),
:deep(.compare-cascader .n-base-selection__state-border),
:deep(.compare-cascader .n-input__wrapper) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
  padding: 0 4px !important;
}

:deep(.compare-cascader) {
  --n-border: transparent !important;
  --n-color: transparent !important;
  --n-font-size: 12px !important;
  --n-placeholder-color: #aaa !important;
}

:deep(.compare-cascader .n-base-selection-placeholder__inner),
:deep(.compare-cascader .n-base-selection-label__render-label) {
  font-size: 12px !important;
  color: #555 !important;
}

:deep(.compare-cascader .n-base-selection-input__content) {
  font-size: 12px !important;
  color: #222 !important;
}

:deep(.compare-cascader .n-base-suffix__arrow svg) {
  width: 14px !important;
  height: 14px !important;
  fill: #888 !important;
}
</style>