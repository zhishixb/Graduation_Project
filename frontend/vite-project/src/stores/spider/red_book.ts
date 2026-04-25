import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMajorList } from '@/apis/spider'

// ==================== 类型定义 ====================
interface MajorItem {
  name: string
  is_processed: number | string | null  // 1 表示已处理，其他表示未处理
}

interface AutoQueueItem {
  name: string
}

interface ProgressState {
  type: number | string
  currentJob: string
  currentPage: number
  currentCount: number
  targetCount: number
}

export const useReadBookStore = defineStore('readBook', () => {
  // ==================== State ====================
  const majorsList = ref<MajorItem[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 级联选择器选项（扁平数据，直接映射）
  const cascaderOptions = computed(() => {
    if (!Array.isArray(majorsList.value)) return []
    return majorsList.value.map((item, index) => ({
      label: item.name || '未命名',
      value: item.name || `option_${index}`,
      disabled: item.is_processed === 1 || item.is_processed === '1'
    }))
  })

  const selectedPositionUid = ref<string | number | null>(null)
  const selectedPosition = ref<MajorItem | null>(null)

  // 爬虫运行状态
  const isRunning = ref(false)
  const isAutoRunning = ref(false)
  const contentText = ref('就绪')
  const contentColor = ref('#999')
  const logs = ref<string[]>([])
  const percent = ref(0)
  const currentPosition = ref('')
  const autoQueue = ref<AutoQueueItem[]>([])
  const isLoadingData = computed(() => isLoading.value)

  // WebSocket 实例
  let ws: WebSocket | null = null
  const AUTO_TASK_DELAY = 120000      // 每个专业完成后默认等待时间（毫秒）
  const EXTRA_PAUSE_AFTER_ROUND = 120000  // 每完成3个专业后额外暂停时间（毫秒）
  let stopRequested = false

  // 自动模式计数器（记录已成功完成的专业数量）
  let autoCompletedCount = 0

  // 进度状态
  const progressState = ref<ProgressState>({
    type: '',
    currentJob: '--',
    currentPage: 0,
    currentCount: 0,
    targetCount: 0
  })

  // ==================== Getters ====================
  const allCompleted = computed(() => {
    if (!Array.isArray(majorsList.value)) return false
    return majorsList.value.every(item => item.is_processed === 1 || item.is_processed === '1')
  })

  // ==================== Actions ====================
  function addLog(msg: string) {
    logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${msg}`)
    if (logs.value.length > 50) logs.value.pop()
  }

  function updateContent(text: string, color: string) {
    contentText.value = text
    contentColor.value = color
  }

  // 获取专业列表
  const fetchMajorsList = async () => {
    isLoading.value = true
    error.value = null
    try {
      const res = await getMajorList()
      let rawData = res?.data || res
      let parsedData: MajorItem[] = []

      if (typeof rawData === 'string') {
        try {
          parsedData = JSON.parse(rawData)
        } catch (e) {
          throw new Error('返回数据格式错误：无法解析 JSON')
        }
      } else if (Array.isArray(rawData)) {
        parsedData = rawData
      } else {
        throw new Error('返回数据不是数组')
      }

      if (!Array.isArray(parsedData)) {
        throw new Error('解析后的数据不是数组')
      }

      majorsList.value = parsedData
      console.log(`加载成功，共 ${parsedData.length} 个专业`)

      if (allCompleted.value) {
        updateContent('全部专业已处理', '#52c41a')
      } else {
        updateContent('数据就绪，请选择专业', '#37ddbf')
      }
    } catch (err: any) {
      error.value = err.message || '获取数据失败'
      console.error(err)
      majorsList.value = []
      updateContent('加载失败', '#ff4d4f')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 选择专业
  const selectPosition = (uid: string | number | null) => {
    if (isAutoRunning.value || allCompleted.value) return

    if (uid === null) {
      selectedPositionUid.value = null
      selectedPosition.value = null
      updateContent('等待选择...', '#969696')
      logs.value = []
      return
    }

    const found = majorsList.value.find(item => item.name === uid)
    if (found && !(found.is_processed === 1 || found.is_processed === '1')) {
      selectedPositionUid.value = uid
      selectedPosition.value = found
      updateContent(`目标：${found.name}`, '#6cb1ff')
      logs.value = [`已锁定：${found.name}`]
    } else {
      selectedPositionUid.value = null
      selectedPosition.value = null
      console.warn('尝试选中已禁用的专业:', uid)
    }
  }

  // 构建自动队列（所有未处理的专业）
  function prepareAutoQueue(): AutoQueueItem[] {
    if (!Array.isArray(majorsList.value) || allCompleted.value) return []
    return majorsList.value
      .filter(item => !(item.is_processed === 1 || item.is_processed === '1'))
      .map(item => ({ name: item.name }))
  }

  // 爬取单个专业（WebSocket）
  function runSingleMajor(majorName: string, onMessage: Function, onError: Function): Promise<void> {
    return new Promise((resolve, reject) => {
      if (ws) {
        ws.onclose = null
        ws.close()
        ws = null
      }

      const taskId = `task_${Date.now()}`
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = 'localhost:8090'
      const wsUrl = `${protocol}//${host}/ws/task/${taskId}`

      ws = new WebSocket(wsUrl)
      let finished = false

      ws.onopen = () => {
        addLog(`[连接] ${majorName}`)
        const startPayload = {
          action: 'start',
          type: 'redbook',
          major: majorName
        }
        ws?.send(JSON.stringify(startPayload))
      }

      ws.onmessage = (event) => {
        try {
          const response = JSON.parse(event.data)
          if (!response.success) {
            onError?.(response.message || '操作失败')
            addLog(`[错误] ${majorName}: ${response.message}`)
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

            if (progressState.value.type === 0) {
              updateContent("正在获取帖子列表", "#283c68")
            } else if (progressState.value.type === 1) {
              if (progressState.value.targetCount > 0) {
                percent.value = Math.min(100, Math.round((progressState.value.currentCount / progressState.value.targetCount) * 100))
              }
              const remainText = isAutoRunning.value ? `[剩${autoQueue.value.length}] ` : ''
              updateContent(`${remainText}${progressState.value.currentJob} (${progressState.value.currentCount}/${progressState.value.targetCount})`, '#6cb1ff')
            } else if (progressState.value.type === 2) {
              addLog(`[完成] ${majorName}`)
              if (!finished) {
                finished = true
                resolve()
              }
            }
          } else if (response.message.includes('started')) {
            onMessage?.(response.message, 'success')
            addLog(`[启动] ${majorName}`)
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

      ws.onerror = (err) => {
        console.error('WS Error:', err)
        addLog(`[错误] ${majorName} 连接异常`)
        if (!finished) {
          finished = true
          reject(new Error('WebSocket 连接错误'))
        }
      }

      ws.onclose = () => {
        if (!finished && !stopRequested) {
          addLog(`[异常] ${majorName} 连接意外关闭`)
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
    currentPosition.value = nextItem.name
    updateContent(`自动模式: ${nextItem.name} (剩余${autoQueue.value.length})`, '#722ed1')
    addLog(`[自动] 开始爬取: ${nextItem.name}`)

    try {
      await runSingleMajor(nextItem.name, onMessage, onError)

      // 一个专业成功完成，计数加1
      autoCompletedCount++
      addLog(`[自动] 已完成 ${autoCompletedCount} 个专业`)

      // 每完成 3 个专业（即 autoCompletedCount % 3 === 0）且还有剩余任务时，额外暂停一次
      const shouldExtraPause = (autoCompletedCount % 3 === 0) && isAutoRunning.value && !stopRequested && autoQueue.value.length > 0
      if (shouldExtraPause) {
        updateContent(`已完成 ${autoCompletedCount} 个专业，暂停 2 分钟...`, '#ff9d4d')
        addLog(`[自动] 每三轮额外暂停 ${EXTRA_PAUSE_AFTER_ROUND / 1000} 秒`)
        await new Promise(resolve => setTimeout(resolve, EXTRA_PAUSE_AFTER_ROUND))
      }

      // 原有的每个专业之间的间隔
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
      addLog(`[自动] ${nextItem.name} 失败: ${err}`)
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
    currentPosition.value = ''
    stopRequested = false
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    progressState.value = { type: '', currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 }
    percent.value = 0
    updateContent('全部自动任务完成', '#52c41a')
    addLog('自动队列执行完毕')
    onMessage?.('自动爬取全部完成', 'success')
    fetchMajorsList()
  }

  async function handleTaskEnd(onMessage?: Function) {
    isRunning.value = false
    isAutoRunning.value = false
    progressState.value = { type: '', currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 }
    percent.value = 0
    selectedPositionUid.value = null
    selectedPosition.value = null
    updateContent('等待选择...', '#969696')
    logs.value = []
    if (ws) {
      ws.close()
      ws = null
    }
    onMessage?.('爬虫运行结束', 'info')
    await fetchMajorsList()
  }

  // 开始任务（手动/自动）
  const startTask = async (
    position: MajorItem | null,
    autoMode: boolean,
    onMessage?: (msg: string, type?: string) => void,
    onError?: (errMsg: string) => void
  ) => {
    if (isRunning.value) {
      onError?.('任务正在运行中')
      return
    }
    if (autoMode && allCompleted.value) {
      onError?.('所有专业均已完成，无可爬取任务')
      return
    }
    stopRequested = false

    if (autoMode) {
      const queue = prepareAutoQueue()
      if (queue.length === 0) {
        onError?.('没有可用的专业（所有专业状态均为已完成）')
        return
      }
      // 重置计数器
      autoCompletedCount = 0
      autoQueue.value = queue
      isAutoRunning.value = true
      isRunning.value = true
      updateContent(`自动模式：共 ${queue.length} 个专业`, '#722ed1')
      addLog(`自动队列生成完毕，将依次爬取 ${queue.length} 个专业`)
      processNextInQueue(onMessage, onError)
    } else {
      if (!position) {
        onError?.('请先选择一个专业')
        return
      }
      isRunning.value = true
      isAutoRunning.value = false
      currentPosition.value = position.name
      updateContent(`正在启动: ${position.name}`, '#6c84ff')
      addLog(`[手动] 开始任务: ${position.name}`)
      try {
        await runSingleMajor(position.name, onMessage, onError)
        await handleTaskEnd(onMessage)
      } catch (err) {
        onError?.(String(err))
        await handleTaskEnd(onMessage)
      }
    }
  }

  // 停止任务
  const stopTask = (callback?: (msg: string, type?: string) => void) => {
    if (!isRunning.value) {
      callback?.('没有正在运行的任务', 'warning')
      return
    }
    if (isAutoRunning.value) {
      stopRequested = true
      updateContent('正在停止自动模式，完成当前任务后结束', '#ff9d4d')
      addLog('手动停止自动模式')
      callback?.('已请求停止，当前任务完成后结束', 'info')
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        finishAuto(callback)
      } else {
        try {
          ws?.send(JSON.stringify({ action: 'stop' }))
        } catch (e) {}
      }
    } else {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'stop' }))
      }
      updateContent('正在关闭爬虫，本轮结束后停止', '#ffcc6c')
      callback?.('本轮结束后爬虫停止', 'info')
    }
  }

  // 清理资源
  const dispose = () => {
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    isRunning.value = false
    isAutoRunning.value = false
    stopRequested = false
    logs.value = []
  }

  return {
    majorsList,
    isLoading,
    error,
    cascaderOptions,
    selectedPositionUid,
    selectedPosition,
    isRunning,
    isAutoRunning,
    contentText,
    contentColor,
    logs,
    percent,
    currentPosition,
    autoQueue,
    isLoadingData,
    allCompleted,
    fetchMajorsList,
    selectPosition,
    startTask,
    stopTask,
    dispose
  }
})