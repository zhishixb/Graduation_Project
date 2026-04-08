import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getJobList } from '@/apis/spider'

// ==================== 类型定义 ====================
interface MajorDetail {
  id: string
  uid?: number          // 新增唯一数字ID
  count: number
  state: string
}

interface RawDataMap {
  [category: string]: {
    [secondary: string]: {
      [position: string]: MajorDetail
    }
  }
}

interface CascaderOption {
  label: string
  value: string          // 使用 uid 的字符串形式
  disabled?: boolean
  children?: CascaderOption[]
  _fullPath?: {
    category: string
    secondary: string
    major: string
    id: string
    uid: number
  }
}

interface MajorPathInfo {
  category: string
  secondary: string
  major: string
  id: string
  uid: number
}

interface ProgressState {
  type: number | string
  currentJob: string
  currentPage: number
  currentCount: number
  targetCount: number
}

interface AutoQueueItem {
  uid: number
  position: string
  pathInfo: MajorPathInfo
}

function isRawDataMap(obj: unknown): obj is RawDataMap {
  if (typeof obj !== 'object' || obj === null) return false
  for (const key in obj) {
    const secondLevel = obj[key]
    if (typeof secondLevel !== 'object' || secondLevel === null) return false
    for (const subKey in secondLevel) {
      const thirdLevel = secondLevel[subKey]
      if (typeof thirdLevel !== 'object' || thirdLevel === null) return false
      for (const finalKey in thirdLevel) {
        const detail = thirdLevel[finalKey]
        if (typeof detail !== 'object' || detail === null || !('state' in detail)) return false
      }
    }
  }
  return true
}

export const useJobByPositionStore = defineStore('jobByPosition', () => {
  // ==================== State ====================
  const rawCascaderData = ref<RawDataMap | null>(null)
  const selectedPositionUid = ref<number | null>(null)   // 存储选中的 uid
  const isLoadingData = ref(false)
  const isRunning = ref(false)
  const isAutoRunning = ref(false)
  const autoQueue = ref<AutoQueueItem[]>([])   // 自动队列存储完整信息
  const currentPosition = ref<string | null>(null)       // 当前爬取的职位名称（用于显示）
  const ws = ref<WebSocket | null>(null)

  // UI 反馈
  const contentText = ref('等待选择...')
  const contentColor = ref('#969696')
  const logs = ref<string[]>([])

  const progressState = ref<ProgressState>({
    type: '',
    currentJob: '--',
    currentPage: 0,
    currentCount: 0,
    targetCount: 0,
  })
  const percent = ref(0)

  const AUTO_TASK_DELAY = 8000
  let stopRequested = false

  // ==================== Getters ====================
  // 级联选项（使用 uid 作为 value）
  const cascaderOptions = computed<CascaderOption[]>(() => {
    if (!rawCascaderData.value) return []
    const options: CascaderOption[] = []
    if (!isRawDataMap(rawCascaderData.value)) {
      console.error('rawCascaderData 数据格式不正确')
      return []
    }
    Object.entries(rawCascaderData.value).forEach(([category, secondaries]) => {
      const categoryNode: CascaderOption = { label: category, value: category, children: [] }
      Object.entries(secondaries).forEach(([secondary, majors]) => {
        const secondaryNode: CascaderOption = { label: secondary, value: secondary, children: [] }
        Object.entries(majors).forEach(([position, detail]) => {
          const isPending = detail.state === 'pending'
          const uid = detail.uid
          if (uid === undefined) {
            console.warn(`职位 ${position} 缺少 uid，将跳过`)
            return
          }
          secondaryNode.children!.push({
            label: position,
            value: String(uid),           // 使用 uid 字符串作为唯一值
            disabled: !isPending,
            _fullPath: { category, secondary, major: position, id: detail.id, uid },
          })
        })
        if (secondaryNode.children!.length) categoryNode.children!.push(secondaryNode)
      })
      if (categoryNode.children!.length) options.push(categoryNode)
    })
    return options
  })

  // uid 到完整路径信息的映射
  const majorPathMap = computed<Map<number, MajorPathInfo>>(() => {
    const map = new Map<number, MajorPathInfo>()
    if (!rawCascaderData.value) return map
    if (!isRawDataMap(rawCascaderData.value)) {
      console.warn('majorPathMap 构建时数据格式不正确')
      return map
    }
    for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
      for (const [secondary, majors] of Object.entries(secondaries)) {
        for (const [major, detail] of Object.entries(majors)) {
          if (detail.uid !== undefined) {
            map.set(detail.uid, { category, secondary, major, id: detail.id, uid: detail.uid })
          }
        }
      }
    }
    return map
  })

  // 辅助：根据 uid 获取职位名称
  function getPositionNameByUid(uid: number): string {
    return majorPathMap.value.get(uid)?.major ?? '未知职位'
  }

  // ==================== Actions ====================
  function addLog(msg: string) {
    logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${msg}`)
    if (logs.value.length > 50) logs.value.pop()
  }

  function updateContent(text: string, color: string) {
    contentText.value = text
    contentColor.value = color
  }

  async function fetchCountJobs() {
    isLoadingData.value = true
    try {
      const res = await getJobList()
      if (res && typeof res === 'object' && 'success' in res) {
        if (res.success && res.data && isRawDataMap(res.data)) {
          rawCascaderData.value = res.data
          updateContent('数据就绪，请选择专业', '#37ddbf')
          console.log('✅ 数据加载成功，条目数:', Object.keys(res.data).length)
        } else {
          rawCascaderData.value = {}
          updateContent(res.message || '数据格式不正确', '#ff4d4f')
          console.warn('⚠️ 数据格式不正确:', res.data)
        }
      } else {
        rawCascaderData.value = {}
        updateContent('API响应异常', '#ff4d4f')
      }
    } catch (e) {
      console.error('❌ 请求失败:', e)
      updateContent('加载失败', '#ff4d4f')
      throw e
    } finally {
      isLoadingData.value = false
    }
  }

  // 选择职位：value 是 uid 字符串
  function selectPosition(value: string | null) {
    if (isAutoRunning.value) return
    if (value === null) {
      selectedPositionUid.value = null
      updateContent('等待选择...', '#969696')
      logs.value = []
      return
    }
    const uid = Number(value)
    if (isNaN(uid)) {
      console.warn('无效的 uid', value)
      return
    }
    const pathInfo = majorPathMap.value.get(uid)
    if (pathInfo) {
      selectedPositionUid.value = uid
      updateContent(`目标：${pathInfo.category} - ${pathInfo.secondary} - ${pathInfo.major}`, '#6cb1ff')
      logs.value = [`已锁定：${pathInfo.category} / ${pathInfo.secondary} / ${pathInfo.major}`]
    } else {
      selectedPositionUid.value = null
      updateContent(`目标：${value} (路径未知)`, '#969696')
    }
  }

  // 构建自动队列：返回所有 pending 职位的 AutoQueueItem[]
  function prepareAutoQueue(): AutoQueueItem[] {
    if (!rawCascaderData.value) return []
    const queue: AutoQueueItem[] = []
    for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
      for (const [secondary, majors] of Object.entries(secondaries)) {
        for (const [position, detail] of Object.entries(majors)) {
          if (detail.state === 'pending' && detail.uid !== undefined) {
            queue.push({
              uid: detail.uid,
              position,
              pathInfo: { category, secondary, major: position, id: detail.id, uid: detail.uid },
            })
          }
        }
      }
    }
    return queue
  }

  // 处理单个职位爬取（接收 uid）
  function runSinglePosition(uid: number, onMessage: Function, onError: Function): Promise<void> {
    return new Promise((resolve, reject) => {
      const pathInfo = majorPathMap.value.get(uid)
      if (!pathInfo) {
        reject(new Error(`找不到 uid 对应的路径: ${uid}`))
        return
      }
      const positionName = pathInfo.major

      // 关闭旧连接
      if (ws.value) {
        ws.value.onclose = null
        ws.value.close()
        ws.value = null
      }

      const taskId = `task_${Date.now()}`
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = 'localhost:8090'
      const wsUrl = `${protocol}//${host}/ws/task/${taskId}`

      ws.value = new WebSocket(wsUrl)
      let finished = false

      ws.value.onopen = () => {
        addLog(`[连接] ${positionName}`)
        const startPayload = {
          action: 'start',
          type: 'position',
          subject: pathInfo.category,
          secondary_subject: pathInfo.secondary,
          major: positionName,
        }
        ws.value?.send(JSON.stringify(startPayload))
      }

      ws.value.onmessage = (event) => {
        try {
          const response = JSON.parse(event.data)
          if (!response.success) {
            onError?.(response.message || '操作失败')
            addLog(`[错误] ${positionName}: ${response.message}`)
            if (!finished) {
              finished = true
              reject(new Error(response.message))
            }
            return
          }
          const data = response.data
          if (!data) return

          if (response.message === 'progress_update') {
            progressState.value.type = data.type || 0
            progressState.value.currentJob = data.current_job || '--'
            progressState.value.currentPage = data.current_page || 0
            progressState.value.currentCount = data.current_count || 0
            progressState.value.targetCount = data.target_count || 0

            if (progressState.value.type === 1) {
              if (progressState.value.targetCount > 0) {
                percent.value = Math.min(100, Math.round((progressState.value.currentCount / progressState.value.targetCount) * 100))
              }
              const remainText = isAutoRunning.value ? `[剩${autoQueue.value.length}] ` : ''
              updateContent(`${remainText}${progressState.value.currentJob} (${progressState.value.currentCount}/${progressState.value.targetCount})`, '#6cb1ff')
            } else if (progressState.value.type === 2) {
              addLog(`[完成] ${positionName}`)
              if (!finished) {
                finished = true
                resolve()
              }
            }
          } else if (response.message.includes('started')) {
            onMessage?.(response.message, 'success')
            addLog(`[启动] ${positionName}`)
          } else if (response.message.includes('Finished') || response.message.includes('Stop')) {
            if (!finished) {
              finished = true
              resolve()
            }
          } else {
            addLog(`[系统] ${response.message}`)
          }
        } catch (e) {
          console.error('消息解析错误:', e, event.data)
        }
      }

      ws.value.onerror = (err) => {
        console.error('WS Error:', err)
        addLog(`[错误] ${positionName} 连接异常`)
        if (!finished) {
          finished = true
          reject(new Error('WebSocket 连接错误'))
        }
      }

      ws.value.onclose = () => {
        if (!finished && !stopRequested) {
          addLog(`[异常] ${positionName} 连接意外关闭`)
          reject(new Error('连接意外关闭'))
        }
      }
    })
  }

  // 处理自动队列中的下一个
  async function processNextInQueue(onMessage: Function, onError: Function) {
    if (!isAutoRunning.value || stopRequested) {
      finishAuto(onMessage)
      return
    }
    if (autoQueue.value.length === 0) {
      finishAuto(onMessage)
      return
    }

    const nextItem = autoQueue.value.shift()!
    currentPosition.value = nextItem.position
    updateContent(`🤖 自动模式: ${nextItem.position} (剩余${autoQueue.value.length})`, '#722ed1')
    addLog(`[自动] 开始爬取: ${nextItem.position}`)

    try {
      await runSinglePosition(nextItem.uid, onMessage, onError)
      if (isAutoRunning.value && !stopRequested && autoQueue.value.length > 0) {
        updateContent(`等待 ${AUTO_TASK_DELAY / 1000} 秒后继续...`, '#ffcc6c')
        await new Promise(resolve => setTimeout(resolve, AUTO_TASK_DELAY))
        processNextInQueue(onMessage, onError)
      } else if (autoQueue.value.length === 0) {
        finishAuto(onMessage)
      } else if (stopRequested) {
        finishAuto(onMessage)
      }
    } catch (err) {
      addLog(`[自动] ${nextItem.position} 失败: ${err}`)
      if (isAutoRunning.value && !stopRequested) {
        await new Promise(resolve => setTimeout(resolve, AUTO_TASK_DELAY))
        processNextInQueue(onMessage, onError)
      } else {
        finishAuto(onMessage)
      }
    }
  }

  function finishAuto(onMessage?: Function) {
    isAutoRunning.value = false
    isRunning.value = false
    currentPosition.value = null
    stopRequested = false
    if (ws.value) {
      ws.value.onclose = null
      ws.value.close()
      ws.value = null
    }
    progressState.value = { type: '', currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 }
    percent.value = 0
    updateContent('🎉 全部自动任务完成', '#52c41a')
    addLog('自动队列执行完毕')
    onMessage?.('自动爬取全部完成', 'success')
    fetchCountJobs()
  }

  function stopTask(onMessage?: Function) {
    if (!isRunning.value) {
      onMessage?.('没有正在运行的任务', 'warning')
      return
    }
    if (isAutoRunning.value) {
      stopRequested = true
      updateContent('正在停止自动模式，完成当前任务后结束', '#ff9d4d')
      addLog('手动停止自动模式')
      onMessage?.('已请求停止，当前任务完成后结束', 'info')
      if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
        finishAuto(onMessage)
      } else {
        try {
          ws.value?.send(JSON.stringify({ action: 'stop' }))
        } catch (e) {}
      }
    } else {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ action: 'stop' }))
      }
      updateContent('正在关闭爬虫，本轮结束后停止', '#ffcc6c')
      onMessage?.('本轮结束后爬虫停止', 'info')
    }
  }

  async function handleTaskEnd(onMessage?: Function) {
    isRunning.value = false
    isAutoRunning.value = false
    progressState.value = { type: '', currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 }
    percent.value = 0
    selectedPositionUid.value = null
    updateContent('等待选择...', '#969696')
    logs.value = []
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    onMessage?.('爬虫运行结束', 'info')
    await fetchCountJobs()
  }

  async function startTask(
    positionUidStr: string | null,    // 手动模式传入 uid 字符串（来自 cascader 的 value）
    autoMode: boolean,
    onMessage: (msg: string, type?: 'success' | 'error' | 'info' | 'warning') => void,
    onError?: (msg: string) => void
  ) {
    if (isRunning.value) {
      onError?.('任务正在运行中')
      return
    }
    stopRequested = false

    if (autoMode) {
      const queue = prepareAutoQueue()
      if (queue.length === 0) {
        onError?.('没有可用的职位（所有职位状态均为 completed）')
        return
      }
      autoQueue.value = queue
      isAutoRunning.value = true
      isRunning.value = true
      updateContent(`🤖 自动模式：共 ${queue.length} 个职位`, '#722ed1')
      addLog(`自动队列生成完毕，将依次爬取 ${queue.length} 个职位`)
      processNextInQueue(onMessage, onError)
    } else {
      if (!positionUidStr) {
        onError?.('请先选择一个职位')
        return
      }
      const uid = Number(positionUidStr)
      if (isNaN(uid)) {
        onError?.('无效的职位标识')
        return
      }
      const pathInfo = majorPathMap.value.get(uid)
      if (!pathInfo) {
        onError?.('职位信息丢失，请刷新页面重试')
        return
      }
      isRunning.value = true
      isAutoRunning.value = false
      currentPosition.value = pathInfo.major
      updateContent(`正在启动: ${pathInfo.major}`, '#6c84ff')
      addLog(`[手动] 开始任务: ${pathInfo.major}`)
      try {
        await runSinglePosition(uid, onMessage, onError)
        await handleTaskEnd(onMessage)
      } catch (err) {
        onError?.(String(err))
        await handleTaskEnd(onMessage)
      }
    }
  }

  function dispose() {
    if (ws.value) {
      ws.value.onclose = null
      ws.value.close()
      ws.value = null
    }
    isRunning.value = false
    isAutoRunning.value = false
    stopRequested = false
    logs.value = []
  }

  return {
    // state
    rawCascaderData,
    selectedPositionUid,        // 改为 uid 存储
    isLoadingData,
    isRunning,
    isAutoRunning,
    autoQueue,
    currentPosition,
    contentText,
    contentColor,
    logs,
    progressState,
    percent,
    // getters
    cascaderOptions,
    majorPathMap,
    // actions
    fetchCountJobs,
    selectPosition,
    startTask,
    stopTask,
    dispose,
  }
})