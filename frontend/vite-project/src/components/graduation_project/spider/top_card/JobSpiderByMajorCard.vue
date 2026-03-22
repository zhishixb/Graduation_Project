<template>
  <div class="search-spider-card" id="spider-major-51job-card-container">
    <!-- 左侧：标题与状态 -->
    <div class="start-card-left">
      <div class="search-spider-card-title">
        {{ isAutoRunning ? '自动批量爬取' : '51Job专业爬取' }}
      </div>

      <!-- 跑马灯组件 -->
      <div class="search-spider-card-state">
        <MarqueeText :text="contentText" :speed="3.5" :color="contentColor" />
      </div>

      <div style="height: 30px">
        <transition name="fade">
          <div v-show="logs.length > 0" class="signal-log-area">
            <div class="log-entry">{{ logs[0] }}</div>
          </div>
        </transition>
      </div>

      <!-- 按钮区域 -->
      <div class="start-card-info-placeholder">
        <!-- 手动/启动按钮 -->
        <n-button
          strong
          secondary
          :type="isRunning ? 'info' : 'error'"
          :loading="isRunning"
          style="border-radius: 30px; height: 30px; font-size: 10px; width: 100%; margin-top: 4px"
          @click="handleStartClick"
        >
          {{ isRunning ? '运行中' : '开始爬取' }}
        </n-button>
      </div>
    </div>

    <!-- 右侧：选择器与控制区 -->
    <div
      class="start-card-right"
    >
      <!-- 级联选择器 (非运行状态显示) -->
      <n-cascader
        v-model:value="selectedMajorName"
        :options="cascaderOptions"
        placeholder="选专业"
        size="small"
        clearable
        :disabled="isLoadingData || isRunning || isAutoRunning"
        :filterable="true"
        :show-path="true"
        :emit-path="false"
        style="width: 100%; margin-top: -10px"
        to="#spider-major-51job-card-container"
        placement="bottom-end"
        strategy="fixed"
        @update:value="handleMajorChange"
        v-if="!isRunning && !isAutoRunning"
      />

      <!-- 自动化配置 Checkbox (仅在空闲时显示) -->
      <div v-if="!isRunning && !isAutoRunning" style="display: flex; gap: 5px; align-items: center;">
         <n-checkbox v-model:checked="useAutoMode" size="small" style="font-size: 10px; transform: scale(0.9)">自动</n-checkbox>
         <n-tooltip trigger="hover">
            <template #trigger>
              <div style="font-size: 16px; color: #999; cursor: help; line-height: 0;">
                <n-icon><AlertCircleOutline /></n-icon>
              </div>
            </template>
            开启后将按顺序爬取所有状态为“可用”的专业
         </n-tooltip>
      </div>

      <!-- 加载提示 -->
      <div v-if="isLoadingData && !isAutoRunning" class="loading-tip">加载数据中...</div>

      <!-- 运行状态展示 (进度条 + 手动暂停) -->
      <transition name="fade">
        <div class="right-running-status" v-if="isRunning">
          <n-progress
              :style="{
                width: '40px',
                '--n-font-size-circle': '10px',
                '--n-icon-size-circle': '36px'
              }"
              type="circle"
              :stroke-width="15"
              :percentage="percent"
              processing
          />
          <div style="font-size: 9px; text-align: center;">正在爬取:<br/>{{selectedMajorName}}</div>
          <n-button
            strong
            secondary
            type="warning"
            size="small"
            style="width: 100%; height: 30px; font-size: 10px; border-radius: 30px"
            @click="handleStopClick"
          >
            暂停
          </n-button>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMessage } from 'naive-ui'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import MarqueeText from "@/components/public/MarqueeText.vue";
import {getMajorsList} from "@/apis/spider.ts";
import {AlertCircleOutline} from "@vicons/ionicons5"

// --- 类型定义 ---
interface MajorDetail { state: number; [key: string]: any }
interface RawDataMap { [category: string]: { [secondary: string]: { [majorName: string]: MajorDetail } } }
interface CascaderOption { label: string; value: string; disabled?: boolean; children?: CascaderOption[]; _fullPath?: { category: string; secondary: string; major: string } }
interface MajorPathInfo { category: string; secondary: string; }

// 类型守卫
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

// --- 状态变量 ---
const message = useMessage()
const rawCascaderData = ref<RawDataMap | null>(null)
const selectedMajorName = ref<string | null>(null)
const isLoadingData = ref(false)
const contentText = ref('等待选择...')
const contentColor = ref('#969696')
const logs = ref<string[]>([])
const isRunning = ref(false)
const ws = ref<WebSocket | null>(null)
const percent = ref(0)

const progressState = ref({ type: '', currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 })

// --- 自动化相关状态 ---
const useAutoMode = ref(false)
const isAutoRunning = ref(false)
const autoQueue = ref<string[]>([])
const currentAutoMajor = ref<string | null>(null)
const AUTO_TASK_DELAY = 8000 // 3秒间隔

// --- 计算属性 ---
const queueRemaining = computed(() => autoQueue.value.length);

// --- 业务逻辑：获取数据 ---
const fetchCountJobs = async () => {
  try {
    isLoadingData.value = true
    const res = await getMajorsList()

    if (res && typeof res === 'object' && 'success' in res) {
      if (res.success && res.data && isRawDataMap(res.data)) {
        rawCascaderData.value = res.data
        if (!isAutoRunning.value) {
            contentText.value = '数据就绪，请选择专业'
            contentColor.value = '#37ddbf'
        }
        console.log("✅ 数据加载成功")
      } else {
        handleError("数据格式不正确")
      }
    } else {
      handleError("API响应异常")
    }
  } catch (e) {
    console.error('❌ 请求失败:', e)
    handleError("加载数据失败")
  } finally {
    isLoadingData.value = false
  }
}

const handleError = (msg: string) => {
    rawCascaderData.value = {}
    contentText.value = msg
    contentColor.value = '#ff4d4f'
    if(!isAutoRunning.value) message.error(msg)
}

// --- 业务逻辑：处理选择 ---
const handleMajorChange = (value: string | null) => {
  if (value) {
    selectedMajorName.value = value
    const pathInfo = majorPathMap.value.get(value)
    if (pathInfo) {
      contentText.value = `目标：${pathInfo.category} - ${pathInfo.secondary} - ${value}`
      contentColor.value = '#6cb1ff'
      logs.value = [`已锁定：${value}`]
    } else {
      contentText.value = `目标：${value} (路径未知)`
    }
  } else {
    selectedMajorName.value = null
    if(!isAutoRunning.value) {
        contentText.value = '等待选择...'
        contentColor.value = '#969696'
        logs.value = []
    }
  }
}

// --- 计算属性：构建级联选项 ---
const cascaderOptions = computed<CascaderOption[]>(() => {
  if (!rawCascaderData.value || !isRawDataMap(rawCascaderData.value)) return []
  const options: CascaderOption[] = []

  try {
    Object.entries(rawCascaderData.value).forEach(([category, secondaries]) => {
      const categoryNode: CascaderOption = { label: category, value: category, children: [] }
      Object.entries(secondaries).forEach(([secondary, majors]) => {
        const secondaryNode: CascaderOption = { label: secondary, value: secondary, children: [] }
        Object.entries(majors).forEach(([majorName, detail]) => {
          const isDisabled = detail.state !== 1
          const majorNode: CascaderOption = {
            label: majorName, value: majorName, disabled: isDisabled,
            _fullPath: { category, secondary, major: majorName }
          }
          secondaryNode.children!.push(majorNode)
        })
        if (secondaryNode.children!.length > 0) categoryNode.children!.push(secondaryNode)
      })
      if (categoryNode.children!.length > 0) options.push(categoryNode)
    })
  } catch (e) {
    console.error("构建级联选项出错:", e)
  }

  return options
})

// --- 计算属性：构建路径映射 ---
const majorPathMap = computed<Map<string, MajorPathInfo>>(() => {
  const map = new Map<string, MajorPathInfo>()
  if (!rawCascaderData.value || !isRawDataMap(rawCascaderData.value)) return map

  try {
    for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
      for (const [secondary, majors] of Object.entries(secondaries)) {
        for (const majorName of Object.keys(majors)) {
          map.set(majorName, { category, secondary })
        }
      }
    }
  } catch (e) {
    console.error("构建路径映射出错:", e)
  }
  return map
})

// --- 准备自动化队列 ---
const prepareAutoQueue = (): string[] => {
  if (!rawCascaderData.value || typeof rawCascaderData.value !== 'object') {
    return []
  }

  const queue: string[] = []
  try {
    for (const [, secondaries] of Object.entries(rawCascaderData.value)) {
      if (!secondaries) continue
      for (const [, majors] of Object.entries(secondaries)) {
        if (!majors) continue
        for (const [majorName, detail] of Object.entries(majors)) {
          // 只加入 state === 1 (可用) 的专业
          if (detail && detail.state === 1) {
            queue.push(majorName)
          }
        }
      }
    }
  } catch (e) {
    console.error("生成队列时出错:", e)
  }
  return queue
}

// --- 点击开始按钮 ---
const handleStartClick = () => {
  if (isRunning.value) {
    message.warning('任务正在运行中')
    return
  }

  try {
    if (useAutoMode.value) {
      startAutoSpider()
    } else {
      startSpider()
    }
  } catch (error) {
    console.error("💥 启动出错:", error)
    message.error(`启动失败: ${error instanceof Error ? error.message : '未知错误'}`)
    isRunning.value = false
    isAutoRunning.value = false
  }
}

// --- 手动启动单个任务 ---
const startSpider = () => {
  // 1. 检查是否选择了专业
  if (!selectedMajorName.value) {
    message.warning('请先在右侧选择一个专业')
    isRunning.value = false // 重置状态，防止按钮卡在 loading
    return
  }

  isRunning.value = true

  // 2. 使用 .value 获取实际字符串
  const pathInfo = majorPathMap.value.get(selectedMajorName.value)

  // 3. 检查路径信息是否存在
  if (!pathInfo) {
    console.error('❌ 无法找到专业路径信息:', selectedMajorName.value)
    message.error('专业数据异常，请刷新重试')
    isRunning.value = false
    fetchCountJobs() // 尝试重新加载
    return
  }

  // 4. 更新 UI 并执行
  logs.value.unshift(`[手动] 开始任务: ${selectedMajorName.value}`)
  contentText.value = `正在启动: ${selectedMajorName.value}...`
  contentColor.value = '#6cb1ff'

  executeSpiderTask(pathInfo, selectedMajorName.value)
}

// --- ✨ 启动自动化流程 ---
const startAutoSpider = () => {
  const queue = prepareAutoQueue()
  if (queue.length === 0) {
    message.warning('没有可用的专业需要爬取 (数据未加载或所有专业已完成)')
    isRunning.value = false
    return
  }

  autoQueue.value = queue
  isAutoRunning.value = true
  isRunning.value = true

  contentText.value = `🤖 自动模式：共 ${queue.length} 个`
  contentColor.value = '#722ed1'
  logs.value = [`队列生成完毕，开始执行...`]

  processNextInQueue()
}

// --- 处理队列中的下一个 ---
const processNextInQueue = () => {
  if (!isAutoRunning.value) return

  if (autoQueue.value.length === 0) {
    finishAutoSpider()
    return
  }

  const nextMajor = autoQueue.value.shift()!
  currentAutoMajor.value = nextMajor
  selectedMajorName.value = nextMajor

  const pathInfo = majorPathMap.value.get(nextMajor)

  // ✅ 关键保护：如果找不到路径，跳过而不是崩溃
  if (!pathInfo) {
    console.warn(`⚠️ 跳过专业 (路径未知): ${nextMajor}`)
    logs.value.unshift(`[跳过] ${nextMajor} 路径不存在`)
    setTimeout(processNextInQueue, 500)
    return
  }

  logs.value.unshift(`[自动] 开始: ${nextMajor}`)
  contentText.value = `正在: ${nextMajor} ...`

  executeSpiderTask(pathInfo, nextMajor)
}

// --- 核心逻辑：执行单个任务 (WebSocket) ---
const executeSpiderTask = (pathInfo: MajorPathInfo, majorName: string) => {
  // 清理旧连接
  if (ws.value) {
    if (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING) {
      ws.value.close()
    }
    ws.value = null
  }

  const taskId = 'task_auto_' + Date.now()
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = 'localhost:8090' // ⚠️ 请确认你的后端地址
  const wsUrl = `${protocol}//${host}/ws/task/${taskId}`

  try {
    ws.value = new WebSocket(wsUrl)
  } catch (e) {
    console.error("WS 创建失败:", e)
    message.error("WebSocket 初始化失败")
    if(isAutoRunning.value) setTimeout(processNextInQueue, 2000)
    else { isRunning.value = false }
    return
  }

  ws.value.onopen = () => {
    if (!ws.value) return
    logs.value.unshift('[连接] 成功，发送指令...')

    // ✅ 此时 pathInfo 肯定存在，因为前面已经检查过
    const startPayload = {
      action: 'start',
      type: 'major',
      subject: pathInfo.category,
      secondary_subject: pathInfo.secondary,
      major: majorName
    }
    ws.value.send(JSON.stringify(startPayload))
  }

  ws.value.onmessage = (event) => {
    try {
      const response = JSON.parse(event.data)

      if (!response.success) {
        const errMsg = response.message || '操作失败'
        logs.value.unshift(`[错误] ${majorName}: ${errMsg}`)

        if (isAutoRunning.value) {
           setTimeout(processNextInQueue, 1000)
        } else {
           message.error(errMsg)
           handleTaskEnd()
        }
        return
      }

      const data = response.data
      console.log(data)
      if (!data) return

      if (response.message === 'progress_update') {
        progressState.value.type = data.type || 0
        progressState.value.currentJob = data.current_job || '--'
        progressState.value.currentPage = data.current_page || 0
        progressState.value.currentCount = data.current_count || 0
        progressState.value.targetCount = data.target_count || 0
      }

      if(progressState.value.type == 1){
        if (progressState.value.targetCount > 0) {
          percent.value = Math.min(100, Math.round((progressState.value.currentCount / progressState.value.targetCount) * 100))
        }
        if(isAutoRunning.value){
          contentText.value = `[剩${queueRemaining.value}] ${progressState.value.currentJob} (${progressState.value.currentCount}/${progressState.value.targetCount})`
        } else {
          contentText.value = `${progressState.value.currentJob} (${progressState.value.currentCount}/${progressState.value.targetCount})`
        }
      } else if (progressState.value.type == 2) {
        if (isAutoRunning.value) {
           logs.value.unshift(`[完成] ${majorName}`)
           setTimeout(() => {
             processNextInQueue()
           }, AUTO_TASK_DELAY)
        } else {
           handleTaskEnd()
        }
      } else {
         logs.value.unshift(`[启动] ${majorName}`)
      }
    } catch (e) {
      console.error('消息解析错误:', e, event.data)
    }
  }

  ws.value.onerror = (err) => {
    console.error('WS Error:', err)
    if(isAutoRunning.value) {
        logs.value.unshift(`[连接错误] ${majorName}`)
        setTimeout(processNextInQueue, 2000)
    } else {
        message.error('连接错误')
        handleTaskEnd()
    }
  }

  ws.value.onclose = () => {
    if (!isAutoRunning.value && isRunning.value) {
       setTimeout(() => { if(isRunning.value) handleTaskEnd() }, 500)
    }
  }
}

const handleStopClick = async () => {
  if(isAutoRunning.value){
    await stopAutoSpider()
  } else {
    await stopSpider()
  }
}

// --- 停止爬虫 (手动) ---
const stopSpider = async () => {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    isRunning.value = false
    return
  }
  ws.value.send(JSON.stringify({ action: 'stop' }))
  contentText.value = "正在停止..."
  message.loading('发送停止指令...')
}

// --- 停止自动化 ---
const stopAutoSpider = () => {
  isAutoRunning.value = false
  useAutoMode.value = false
  if (ws.value) {
    try {
      if(ws.value.readyState === WebSocket.OPEN) ws.value.send(JSON.stringify({ action: 'stop' }))
      else ws.value.close()
    } catch(e) { /* ignore */ }
  }
  message.info('自动化已终止')
  setTimeout(() => {
     if(!isRunning.value) resetUIState()
  }, 500)
}

// --- 自动化全部完成 ---
const finishAutoSpider = () => {
  isAutoRunning.value = false
  useAutoMode.value = false
  currentAutoMajor.value = null
  autoQueue.value = []
  percent.value = 0

  contentText.value = '🎉 全部完成！'
  contentColor.value = '#52c41a'
  logs.value.unshift('[系统] 队列执行完毕')
  message.success('所有任务完成！')

  resetUIState()
  fetchCountJobs()
}

// --- 重置 UI ---
const resetUIState = () => {
  isRunning.value = false
  progressState.value = { type: '', currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 }
  percent.value = 0
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  selectedMajorName.value = null
  if(!isAutoRunning.value) {
      contentText.value = '等待选择...'
      contentColor.value = '#969696'
      logs.value = []
  }
}

// --- 任务结束 (手动模式) ---
const handleTaskEnd = async () => {
  if (isAutoRunning.value) {
    setTimeout(processNextInQueue, AUTO_TASK_DELAY)
    return
  }
  resetUIState()
  message.info("运行结束")
  await fetchCountJobs()
}

onMounted(() => {
  fetchCountJobs()
})

onBeforeUnmount(() => {
  if (ws.value) ws.value.close()
  isAutoRunning.value = false
  isRunning.value = false
})
</script>

<style scoped>
/* 保持原有样式，仅添加少量新样式 */
.search-spider-card {
  width: 230px;
  height: 150px;
  display: flex;
  gap: 12px;
  /* 确保容器不被压缩 */
  flex-shrink: 0;
}
.start-card-left {
  width: 90px;
  height: 120px;
  display: flex;
  flex-direction: column;
  padding: 15px;
}
.start-card-right {
  width: 110px;
  height: 100%;
  display: flex;
  padding: 10px;
  gap: 20px;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 20;
}

.search-spider-card-title {
  font-size: 11px;
  color: #999999;
  margin-bottom: 10px;
}

.search-spider-card-state { height: 25px; margin-bottom: 9px; }
.signal-log-area {
  height: 20px; display: flex; align-items: center; justify-content: center;
  background: #f0faff; border: 1px solid #d6e4ff; border-radius: 4px;
  overflow: hidden; animation: slideIn 0.3s ease-out;
}
.log-entry {
  font-size: 10px; color: #6cb1ff; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; padding: 0 6px;
  width: 100%; text-align: center; font-weight: 500;
}
.start-card-info-placeholder { height: 24px; display: flex; align-items: center; }
.loading-tip { font-size: 9px; color: #999; text-align: center; margin-top: 15px; }
.right-running-status { display: flex; gap: 5px; flex-direction: column; justify-content: center; align-items: center; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-5px); }
@keyframes slideIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

:deep(.n-cascader) { width: 100%; }
:deep(.n-cascader__trigger) {
  height: 30px !important; font-size: 11px !important; border-radius: 6px !important;
  background-color: #f9f9f9; border: 1px solid #e0e0e0; transition: all 0.2s;
}
:deep(.n-cascader__trigger:hover) { background-color: #f0f0f0; border-color: #6cb1ff; }
:deep(.n-cascader__label) { padding-left: 6px; color: #333; }
:deep(.n-cascader-menu) {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important; border-radius: 6px !important;
  border: 1px solid #eee !important; font-size: 12px;
}
</style>