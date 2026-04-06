import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getJobList } from '@/apis/spider'

// 类型定义（不变）
interface MajorDetail {
  id: string
  count: number
  state: string // 'pending' | 'completed'
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
  value: string
  disabled?: boolean
  children?: CascaderOption[]
  _fullPath?: {
    category: string
    secondary: string
    major: string
    id?: string
  }
}

interface MajorPathInfo {
  category: string
  secondary: string
  id?: string
}

interface ProgressState {
  type: number | string
  currentJob: string
  currentPage: number
  currentCount: number
  targetCount: number
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
  // --- State ---
  const rawCascaderData = ref<RawDataMap | null>(null)
  const selectedPosition = ref<string | null>(null)
  const isLoadingData = ref(false)
  const isRunning = ref(false)
  const isAutoRunning = ref(false)       // 自动模式标志
  const autoQueue = ref<string[]>([])    // 自动队列（职位名称）
  const currentPosition = ref<string | null>(null) // 当前正在爬取的职位
  const ws = ref<WebSocket | null>(null)

  // UI 反馈数据
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

  // 自动任务间隔（毫秒）
  const AUTO_TASK_DELAY = 8000
  let stopRequested = false // 手动停止标志

  // --- Getters（级联选项和路径映射与原相同，略）---
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
          secondaryNode.children!.push({
            label: position,
            value: position,
            disabled: !isPending,
            _fullPath: { category, secondary, major: position, id: detail.id },
          })
        })
        if (secondaryNode.children!.length) categoryNode.children!.push(secondaryNode)
      })
      if (categoryNode.children!.length) options.push(categoryNode)
    })
    return options
  })

  const majorPathMap = computed<Map<string, MajorPathInfo>>(() => {
    const map = new Map<string, MajorPathInfo>()
    if (!rawCascaderData.value) return map
    if (!isRawDataMap(rawCascaderData.value)) {
      console.warn('majorPathMap 构建时数据格式不正确')
      return map
    }
    for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
      for (const [secondary, majors] of Object.entries(secondaries)) {
        for (const [position, detail] of Object.entries(majors)) {
          map.set(position, { category, secondary, id: detail.id })
        }
      }
    }
    return map
  })

  // --- Actions ---
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

  function selectPosition(value: string | null) {
    if (isAutoRunning.value) return // 自动运行时禁止手动选择
    selectedPosition.value = value
    if (value) {
      const pathInfo = majorPathMap.value.get(value)
      if (pathInfo) {
        updateContent(`目标：${pathInfo.category} - ${pathInfo.secondary} - ${value}`, '#6cb1ff')
        logs.value = [`已锁定：${pathInfo.category} / ${pathInfo.secondary} / ${value}`]
      } else {
        updateContent(`目标：${value} (路径未知)`, '#969696')
      }
    } else {
      updateContent('等待选择...', '#969696')
      logs.value = []
    }
  }

  // 构建自动队列（所有 state === 'pending' 的职位）
  function prepareAutoQueue(): string[] {
    if (!rawCascaderData.value) return []
    const queue: string[] = []
    for (const [, secondaries] of Object.entries(rawCascaderData.value)) {
      for (const [, majors] of Object.entries(secondaries)) {
        for (const [position, detail] of Object.entries(majors)) {
          if (detail.state === 'pending') {
            queue.push(position)
          }
        }
      }
    }
    return queue
  }

  // 处理单个职位爬取（内部方法）
  function runSinglePosition(position: string, onMessage: Function, onError: Function): Promise<void> {
    return new Promise((resolve, reject) => {
      const pathInfo = majorPathMap.value.get(position)
      if (!pathInfo) {
        reject(new Error(`找不到路径: ${position}`))
        return
      }

      // 关闭旧连接（如果存在）
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
        addLog(`[连接] ${position}`)
        const startPayload = {
          action: 'start',
          type: 'position',
          subject: pathInfo.category,
          secondary_subject: pathInfo.secondary,
          major: position,
        }
        ws.value?.send(JSON.stringify(startPayload))
      }

      ws.value.onmessage = (event) => {
        try {
          const response = JSON.parse(event.data)
          if (!response.success) {
            onError?.(response.message || '操作失败')
            addLog(`[错误] ${position}: ${response.message}`)
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
              // 任务完成
              addLog(`[完成] ${position}`)
              if (!finished) {
                finished = true
                resolve()
              }
            }
          } else if (response.message.includes('started')) {
            onMessage?.(response.message, 'success')
            addLog(`[启动] ${position}`)
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
        addLog(`[错误] ${position} 连接异常`)
        if (!finished) {
          finished = true
          reject(new Error('WebSocket 连接错误'))
        }
      }

      ws.value.onclose = () => {
        if (!finished && !stopRequested) {
          addLog(`[异常] ${position} 连接意外关闭`)
          reject(new Error('连接意外关闭'))
        }
      }
    })
  }

  // 处理队列中的下一个（自动模式）
  async function processNextInQueue(onMessage: Function, onError: Function) {
    if (!isAutoRunning.value || stopRequested) {
      finishAuto(onMessage)
      return
    }
    if (autoQueue.value.length === 0) {
      finishAuto(onMessage)
      return
    }

    const nextPosition = autoQueue.value.shift()!
    currentPosition.value = nextPosition
    updateContent(`🤖 自动模式: ${nextPosition} (剩余${autoQueue.value.length})`, '#722ed1')
    addLog(`[自动] 开始爬取: ${nextPosition}`)

    try {
      await runSinglePosition(nextPosition, onMessage, onError)
      // 成功后等待间隔再处理下一个
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
      addLog(`[自动] ${nextPosition} 失败: ${err}`)
      // 失败后继续下一个（可选：也可停止，这里继续）
      if (isAutoRunning.value && !stopRequested) {
        await new Promise(resolve => setTimeout(resolve, AUTO_TASK_DELAY))
        processNextInQueue(onMessage, onError)
      } else {
        finishAuto(onMessage)
      }
    }
  }

  // 完成自动模式
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
    fetchCountJobs() // 刷新禁用状态
  }

  // 停止任务（手动或自动模式均可）
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
      // 如果当前没有任务在跑（比如等待间隔），直接结束
      if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
        finishAuto(onMessage)
      } else {
        // 发送停止指令给后端（可选）
        try {
          ws.value?.send(JSON.stringify({ action: 'stop' }))
        } catch (e) {}
      }
    } else {
      // 手动模式停止
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ action: 'stop' }))
      }
      updateContent('正在关闭爬虫，本轮结束后停止', '#ffcc6c')
      onMessage?.('本轮结束后爬虫停止', 'info')
      // 等待 onmessage 中收到结束信号后调用 handleTaskEnd
    }
  }

  // 手动模式结束处理
  async function handleTaskEnd(onMessage?: Function) {
    isRunning.value = false
    isAutoRunning.value = false
    progressState.value = { type: '', currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 }
    percent.value = 0
    selectedPosition.value = null
    updateContent('等待选择...', '#969696')
    logs.value = []
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    onMessage?.('爬虫运行结束', 'info')
    await fetchCountJobs()
  }

  // 启动任务（统一入口）
  async function startTask(
    position: string | null,
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
      if (!position) {
        onError?.('请先选择一个职位')
        return
      }
      isRunning.value = true
      isAutoRunning.value = false
      currentPosition.value = position
      updateContent(`正在启动: ${position}`, '#6c84ff')
      addLog(`[手动] 开始任务: ${position}`)
      try {
        await runSinglePosition(position, onMessage, onError)
        await handleTaskEnd(onMessage)
      } catch (err) {
        onError?.(String(err))
        await handleTaskEnd(onMessage)
      }
    }
  }

  // 清理（组件卸载）
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
    selectedPosition,
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