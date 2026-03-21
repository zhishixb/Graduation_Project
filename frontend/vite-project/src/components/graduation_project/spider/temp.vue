<template>
  <div class="search-spider-card" id="spider-major-51job-card-container">
    <!-- 左侧：标题与状态 -->
    <div class="start-card-left">
      <div class="search-spider-card-title">51Job专业爬取</div>

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

      <!-- 开始/运行按钮 -->
      <div class="start-card-info-placeholder">
        <n-button
          strong
          secondary
          :type="isRunning ? 'info' : 'error'"
          :loading="isRunning"
          :style="{
            borderRadius: '30px',
            height: '30px',
            fontSize: '10px',
            width: '100%',
            marginTop: '4px'
          }"
          @click="startSpider"
        >
          {{ isRunning ? '运行中' : '开始爬取' }}
        </n-button>
      </div>
    </div>

    <!-- 右侧：选择器 -->
    <div class="start-card-right">
      <n-cascader
        v-model:value="selectedMajorName"
        :options="cascaderOptions"
        placeholder="选专业"
        size="small"
        clearable
        :disabled="isLoadingData || isRunning"
        :filterable="true"
        :show-path="true"
        :emit-path="false"
        style="width: 100%; margin-top: -10px"
        to="#spider-major-51job-card-container"
        placement="bottom-end"
        strategy="fixed"
        @update:value="handleMajorChange"
        v-if="!isRunning"
      />
      <div v-if="isLoadingData" class="loading-tip">加载数据中...</div>

      <transition name="fade">
        <div class="right-running-status" v-if="isRunning">
          <n-progress
              :style="{
                width: '40px',
                margin: '0 8px 12px 0',
                '--n-font-size-circle': '10px', // 👈 关键：强制覆盖圆圈内的字体大小
                '--n-icon-size-circle': '36px'  // (可选) 如果图标也太大，可以一起调小
              }"
              type="circle"
              :stroke-width="15"
              :percentage="percent"
              processing
          />
          <n-button
            strong
            secondary
            type="warning"
            size="small"
            style="width: 100%; height: 30px; font-size: 10px; border-radius: 30px"
            @click="stopSpider"
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

// --- 类型定义 ---
interface MajorDetail {
  state: number;
  [key: string]: any
}

interface RawDataMap {
  [category: string]: {
    [secondary: string]: {
      [majorName: string]: MajorDetail
    }
  }
}

interface CascaderOption {
  label: string;
  value: string;
  disabled?: boolean;
  children?: CascaderOption[];
  _fullPath?: { category: string; secondary: string; major: string }
}

interface MajorPathInfo {
  category: string;
  secondary: string;
}

// --- 类型守卫 ---
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

const progressState = ref({
  type: '',
  currentJob: '--',       // 当前正在爬取的职位/关键词
  currentPage: 0,         // 当前页码
  currentCount: 0,        // 已抓取数量
  targetCount: 0,         // 目标数量
})

const percent = ref(0)

// --- 业务逻辑：获取数据 ---
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

// --- 业务逻辑：处理选择 ---
const handleMajorChange = (value: string | null) => {
  if (value) {
    selectedMajorName.value = value
    const pathInfo = majorPathMap.value.get(value)

    if (pathInfo) {
      contentText.value = `目标：${pathInfo.category} - ${pathInfo.secondary} - ${value}`
      contentColor.value = '#6cb1ff'
      logs.value = [`已锁定：${pathInfo.category} / ${pathInfo.secondary} / ${value}`]
    } else {
      contentText.value = `目标：${value} (路径未知)`
    }
  } else {
    selectedMajorName.value = null
    contentText.value = '等待选择...'
    contentColor.value = '#969696'
    logs.value = []
  }
}

// --- 计算属性：构建级联选项 ---
const cascaderOptions = computed<CascaderOption[]>(() => {
  if (!rawCascaderData.value) return []
  if (!isRawDataMap(rawCascaderData.value)) return []

  const options: CascaderOption[] = []

  Object.entries(rawCascaderData.value).forEach(([category, secondaries]) => {
    const categoryNode: CascaderOption = { label: category, value: category, children: [] }

    Object.entries(secondaries).forEach(([secondary, majors]) => {
      const secondaryNode: CascaderOption = { label: secondary, value: secondary, children: [] }

      Object.entries(majors).forEach(([majorName, detail]) => {
        // state: 0=未完成/不可用, 1=可用, 2=已完成/锁定 (根据实际业务调整)
        const isDisabled = detail.state !== 1

        const majorNode: CascaderOption = {
          label: majorName,
          value: majorName,
          disabled: isDisabled,
          _fullPath: { category, secondary, major: majorName }
        }
        secondaryNode.children!.push(majorNode)
      })

      if (secondaryNode.children!.length > 0) {
        categoryNode.children!.push(secondaryNode)
      }
    })

    if (categoryNode.children!.length > 0) {
      options.push(categoryNode)
    }
  })

  return options
})

// --- 计算属性：构建路径映射 ---
const majorPathMap = computed<Map<string, MajorPathInfo>>(() => {
  const map = new Map<string, MajorPathInfo>()
  if (!rawCascaderData.value || !isRawDataMap(rawCascaderData.value)) return map

  for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
    for (const [secondary, majors] of Object.entries(secondaries)) {
      for (const majorName of Object.keys(majors)) {
        map.set(majorName, { category, secondary })
      }
    }
  }
  return map
})

// --- 核心逻辑：启动爬虫 ---
const startSpider = async () => {
  if (!selectedMajorName.value) {
    message.warning('请先选择专业')
    return
  }

  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    message.warning('任务正在运行中')
    return
  }

  const taskId = 'task_' + Date.now()
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = 'localhost:8090'
  const wsUrl = `${protocol}//${host}/ws/task/${taskId}`

  ws.value = new WebSocket(wsUrl)
  isRunning.value = true
  logs.value = ['正在连接服务器...']
  contentText.value = '连接建立中...'

  ws.value.onopen = () => {
    console.log('✅ WebSocket 连接已建立')
    logs.value = ['连接成功，发送启动指令...']

    const majorName = selectedMajorName.value
    const pathInfo = majorPathMap.value.get(majorName)
    const startPayload = {
      action: 'start',
      type: 'major',
      subject: pathInfo.category,
      secondary_subject: pathInfo.secondary,
      major: majorName
    }

    ws.value?.send(JSON.stringify(startPayload))
  }

  ws.value.onmessage = (event) => {
    try {
      // 1. 解析外层标准结构 { success, message, data }
      const response = JSON.parse(event.data)

      // 2. 全局检查 success
      if (!response.success) {
        message.error(response.message || '操作失败')
        logs.value.unshift(`[错误] ${response.message}`)
        handleTaskEnd() // 失败则结束
        return
      }

      // 3. 获取内部数据
      const data = response.data
      console.log(data)
      if (!data) return

      // 4. 根据 message 或 data.type 分流处理
      // 方案 A: 推荐根据 message 字段判断语义
      if (response.message === 'progress_update') {
        // --- 📊 处理进度更新 (Type 2) ---
        progressState.value.type = data.type || 0
        progressState.value.currentJob = data.current_job || '--'
        progressState.value.currentPage = data.current_page || 0
        progressState.value.currentCount = data.current_count || 0
        progressState.value.targetCount = data.target_count || 0

        if(progressState.value.type == 1){
          // 计算百分比
          if (progressState.value.targetCount > 0) {
            percent.value = Math.min(100, Math.round(
              (progressState.value.currentCount / progressState.value.targetCount) * 100
            ))
          } else {
            percent.value = 0
          }
          // 更新跑马灯文本
          contentText.value = `正在爬取: ${progressState.value.currentJob} (${progressState.value.currentCount}/${progressState.value.targetCount})`
          contentColor.value = '#6cb1ff'
        }else if(progressState.value.type == 2){
          handleTaskEnd()
        }

      } else if (response.message.includes('started') || response.message.includes('启动')) {
        // --- 🚀 处理启动成功 ---
        message.success(response.message)
        logs.value.unshift(`[系统] ${response.message}`)
        contentText.value = '任务已启动，等待数据...'

      } else if (response.message.includes('Finished') || response.message.includes('Stop') || response.message.includes('完成')) {
        // --- 🏁 处理任务结束 ---
        logs.value.unshift(`[系统] ${response.message}`)
        message.info(response.message)
        handleTaskEnd()
      } else {
        // --- 📝 其他普通日志 ---
        logs.value.unshift(`[系统] ${response.message}`)
      }

    } catch (e) {
      console.error('❌ 消息解析失败:', e, '原始数据:', event.data)
      // 如果解析失败，可能是后端发了非 JSON 字符串，可以做兼容处理
    }
  }

  ws.value.onerror = (error) => {
    console.error('WebSocket 错误:', error)
    message.error('连接发生错误')
    logs.value.unshift('[错误] 连接异常')
    handleTaskEnd()
  }

  ws.value.onclose = () => {
    console.log('WebSocket 连接关闭')
    // 如果是正常结束，handleTaskEnd 已经处理了状态
    // 如果是意外断开且 isRunning 为 true，可能需要提示用户
    if (isRunning.value) {
       // 短暂延迟判断是否是真的结束了，防止瞬间重连抖动
       setTimeout(() => {
         if(isRunning.value) {
            message.warning('连接意外断开')
            handleTaskEnd()
         }
       }, 500)
    }
  }
}

// --- 核心逻辑：停止爬虫 ---
const stopSpider = async () => {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    message.warning('没有正在运行的任务')
    isRunning.value = false
    return
  }

  // 发送停止指令
  ws.value.send(JSON.stringify({ action: 'stop' }))
  contentText.value = "正在关闭爬虫，本轮结束后停止"
  contentColor.value = '#ffcc6c'
  message.loading('本轮结束后爬虫停止')
}

// --- 辅助：任务结束处理 ---
const handleTaskEnd = async () => {
  isRunning.value = false
  // 重置进度条
  progressState.value = {
    type: 0,
    currentJob: '--',
    currentPage: 0,
    currentCount: 0,
    targetCount: 0,
  }
  percent.value = 0

  selectedMajorName.value = null
  contentText.value = '等待选择...'
  contentColor.value = '#969696'
  logs.value = []

  ws.value?.close()
  ws.value = null

  message.info("爬虫运行结束")
  await fetchCountJobs() // 刷新下拉框状态
}

// --- 生命周期 ---
onMounted(() => {
  console.log("🚀 组件挂载，开始初始化...")
  fetchCountJobs()
})

onBeforeUnmount(() => {
  console.log("💀 组件销毁，清理资源...")
  logs.value = []
  rawCascaderData.value = null
})
</script>

<style scoped>
.search-spider-card {
  width: 230px;
  height: 150px;
  display: flex;
  gap: 12px;
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
.search-spider-card-state {
  height: 25px;
  margin-bottom: 9px;
}
.signal-log-area {
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0faff;
  border: 1px solid #d6e4ff;
  border-radius: 4px;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}
.log-entry {
  font-size: 10px;
  color: #6cb1ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 6px;
  width: 100%;
  text-align: center;
  font-weight: 500;
}
.start-card-info-placeholder {
  height: 24px;
  display: flex;
  align-items: center;
}
.loading-tip {
  font-size: 9px;
  color: #999;
  text-align: center;
  margin-top: 15px;
}

.right-running-status{
  display: flex;
  gap: 10px;
  flex-direction: column;
  justify-content: center; /* 垂直居中 */
  align-items: center;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

:deep(.n-cascader) { width: 100%; }
:deep(.n-cascader__trigger) {
  height: 30px !important;
  font-size: 11px !important;
  border-radius: 6px !important;
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  transition: all 0.2s;
}
:deep(.n-cascader__trigger:hover) {
  background-color: #f0f0f0;
  border-color: #6cb1ff;
}
:deep(.n-cascader__label) { padding-left: 6px; color: #333; }
:deep(.n-cascader-menu) {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
  border-radius: 6px !important;
  border: 1px solid #eee !important;
  font-size: 12px;
}
</style>

能添加自动化方法吗（即自动触发startSpider，等待返回完成消息后使用下一个mjorName执行）