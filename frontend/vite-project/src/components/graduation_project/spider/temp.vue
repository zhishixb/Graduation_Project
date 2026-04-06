<template>
  <!-- ID 保持不变 -->
  <div class="search-spider-card" id="spider-job-51job-card-container">

    <div class="start-card-left">
      <div class="search-spider-card-title">51Job岗位爬取</div>

      <div class="search-spider-card-state">
        <MarqueeText :text="contentText" :speed="3.5" :color="contentColor" ></MarqueeText>
      </div>

      <div style="height: 30px">
        <transition name="fade">
          <div v-show="logs.length > 0" class="signal-log-area">
            <div class="log-entry">{{ logs[0] }}</div>
          </div>
        </transition>
      </div>

      <!-- 测试按钮 -->
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
        v-model:value="selectedPosition"
        :options="cascaderOptions"
        placeholder="选职位"
        size="small"
        clearable
        :disabled="isLoadingData || isRunning"
        :filterable="true"
        :show-path="true"
        :emit-path="false"
        style="width: 100%; margin-top: -10px"
        to="#spider-job-51job-card-container"
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
import {getJobList} from "@/apis/spider.ts";

// --- 类型定义 (已更新以适配 JSON 字符串 state) ---
interface MajorDetail {
  id: string;
  count: number;
  state: string; // 修改为字符串: "pending" | "completed"
  [key: string]: any
}

// 结构: { "销售/客服": { "销售管理": { "销售经理": { state: "pending", ... } } } }
interface RawDataMap {
  [category: string]: {
    [secondary: string]: {
      [position: string]: MajorDetail
    }
  }
}

interface CascaderOption {
  label: string;
  value: string;
  disabled?: boolean;
  children?: CascaderOption[];
  _fullPath?: { category: string; secondary: string; major: string; id?: string }
}

// 映射表类型：专业名 -> { category, secondary }
interface MajorPathInfo {
  category: string;
  secondary: string;
  id?: string; // 顺便存储 ID，方便直接调用
}

// --- 类型守卫函数：检查是否为 RawDataMap 类型 ---
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
        // 检查 detail 是否为对象且包含 state 字段 (不限制 state 类型，兼容 string/number)
        if (typeof detail !== 'object' || detail === null || !('state' in detail)) return false;
      }
    }
  }
  return true;
}

// --- 状态变量 ---
const message = useMessage()
const rawCascaderData = ref<RawDataMap | null>(null)
const selectedPosition = ref<string | null>(null)
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

// --- 计算属性：构建级联选项 (核心修改：适配字符串 state) ---
const cascaderOptions = computed<CascaderOption[]>(() => {
  if (!rawCascaderData.value) return []

  const options: CascaderOption[] = []

  if (!isRawDataMap(rawCascaderData.value)) {
    console.error("rawCascaderData 数据格式不正确");
    return [];
  }

  // 第一层：遍历大类 (Category)
  Object.entries(rawCascaderData.value).forEach(([category, secondaries]) => {
    const categoryNode: CascaderOption = {
      label: category,
      value: category,
      children: []
    }

    // 第二层：遍历中类 (Secondary/Sub-category)
    Object.entries(secondaries).forEach(([secondary, majors]) => {
      const secondaryNode: CascaderOption = {
        label: secondary,
        value: secondary,
        children: []
      }

      // 第三层：遍历具体职位 (Position/Major)
      Object.entries(majors).forEach(([position, detail]) => {
        // 【关键修改】适配字符串状态
        // 逻辑：如果 state 不是 'pending' (例如是 'completed')，则禁用
        // 如果您的业务逻辑是 state='0'或'2'禁用，请改回数字判断，但需确保 JSON 里是数字
        const isPending = detail.state === 'pending';
        const isDisabled = !isPending;

        const majorNode: CascaderOption = {
          label: position,
          value: position,
          disabled: isDisabled,
          _fullPath: {
            category,
            secondary,
            major: position,
            id: detail.id // 存储 ID 供后续使用
          }
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

// --- 计算属性：构建专业名到路径的映射表 ---
const majorPathMap = computed<Map<string, MajorPathInfo>>(() => {
  const map = new Map<string, MajorPathInfo>()
  if (!rawCascaderData.value) return map

  if (!isRawDataMap(rawCascaderData.value)) {
    console.warn("majorPathMap 构建时，rawCascaderData 数据格式不正确");
    return map;
  }

  for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
    for (const [secondary, majors] of Object.entries(secondaries)) {
      for (const [position, detail] of Object.entries(majors)) {
        map.set(position, {
          category,
          secondary,
          id: detail.id
        })
      }
    }
  }
  return map
})

// --- 业务逻辑：获取数据 ---
const fetchCountJobs = async () => {
  try {
    const res = await getJobList()

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
    selectedPosition.value = value
    const pathInfo = majorPathMap.value.get(value)

    if (pathInfo) {
      contentText.value = `目标：${pathInfo.category} - ${pathInfo.secondary} - ${value}`
      contentColor.value = '#6cb1ff'
      logs.value = [`已锁定：${pathInfo.category} / ${pathInfo.secondary} / ${value}`]
    } else {
      contentText.value = `目标：${value} (路径未知)`
    }
  } else {
    selectedPosition.value = null
    contentText.value = '等待选择...'
    contentColor.value = '#969696'
    logs.value = []
  }
}

// --- 核心逻辑：启动爬虫线程 ---
const startSpider = async () => {

  const position = selectedPosition.value
  if (!position) {
    message.warning("请先选择具体职位")
    return
  }

  const pathInfo = majorPathMap.value.get(position)
  if (!pathInfo) {
    message.error("无法解析所选职位的路径")
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

    const positionName = selectedPosition.value
    const pathInfo = majorPathMap.value.get(positionName)
    const startPayload = {
      action: 'start',
      type: 'position',
      subject: pathInfo.category,
      secondary_subject: pathInfo.secondary,
      major: positionName
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

        console.log(progressState.value.targetCount)

        if(progressState.value.type == 1){
          // 计算百分比
          if (progressState.value.targetCount > 0) {
            percent.value = Math.min(100, Math.round((progressState.value.currentCount / progressState.value.targetCount) * 100))
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
}

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

  selectedPosition.value = null
  contentText.value = '等待选择...'
  contentColor.value = '#969696'
  logs.value = []

  ws.value?.close()
  ws.value = null

  message.info("爬虫运行结束")
  await fetchCountJobs() // 刷新下拉框状态
}


onMounted(() => {
  fetchCountJobs()
})

onBeforeUnmount(() => {
  logs.value = []
  console.log("组件销毁，内存释放")
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