import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
// 请确保你的 API 路径正确
import { getMajorsList } from "@/apis/spider";

// --- 类型定义 ---
interface MajorDetail { state: number; [key: string]: any }
interface RawDataMap { [category: string]: { [secondary: string]: { [majorName: string]: MajorDetail } } }
interface CascaderOption {
  label: string;
  value: string;
  disabled?: boolean;
  children?: CascaderOption[];
}
interface MajorPathInfo { category: string; secondary: string; }
interface ProgressState {
  type: number;
  currentJob: string;
  currentPage: number;
  currentCount: number;
  targetCount: number;
}

export const useSpiderStore = defineStore('spider', () => {
  // --- State ---
  const rawCascaderData = ref<RawDataMap | null>(null);
  const isLoadingData = ref(false);

  // 运行状态
  const isRunning = ref(false);
  const isAutoRunning = ref(false);
  const currentMajor = ref<string | null>(null);
  const autoQueue = ref<string[]>([]);
  const stopRequested = ref(false);

  // 进度与日志
  const progress = ref<ProgressState>({
    type: 0,
    currentJob: '--',
    currentPage: 0,
    currentCount: 0,
    targetCount: 0
  });
  const logs = ref<string[]>([]);
  const statusText = ref('等待选择...');
  const statusColor = ref('#969696');

  // WebSocket 实例 (非响应式，避免序列化问题)
  let ws: WebSocket | null = null;
  const AUTO_TASK_DELAY = 8000; // 8秒间隔

  // --- Getters ---

  // 1. 计算进度百分比
  const percent = computed(() => {
    if (progress.value.targetCount === 0) return 0;
    return Math.min(100, Math.round((progress.value.currentCount / progress.value.targetCount) * 100));
  });

  // 2. 构建级联选择器选项
  const cascaderOptions = computed<CascaderOption[]>(() => {
    if (!rawCascaderData.value) return [];

    const options: CascaderOption[] = [];
    try {
      Object.entries(rawCascaderData.value).forEach(([category, secondaries]) => {
        const categoryNode: CascaderOption = { label: category, value: category, children: [] };

        Object.entries(secondaries).forEach(([secondary, majors]) => {
          const secondaryNode: CascaderOption = { label: secondary, value: secondary, children: [] };

          Object.entries(majors).forEach(([majorName, detail]) => {
            const isDisabled = detail.state !== 1;
            secondaryNode.children!.push({
              label: majorName,
              value: majorName,
              disabled: isDisabled
            });
          });

          if (secondaryNode.children!.length > 0) {
            categoryNode.children!.push(secondaryNode);
          }
        });

        if (categoryNode.children!.length > 0) {
          options.push(categoryNode);
        }
      });
    } catch (e) {
      console.error("构建级联选项出错:", e);
    }
    return options;
  });

  // 3. 构建路径映射 (用于快速查找)
  const majorPathMap = computed<Map<string, MajorPathInfo>>(() => {
    const map = new Map<string, MajorPathInfo>();
    if (!rawCascaderData.value) return map;
    for (const [category, secondaries] of Object.entries(rawCascaderData.value)) {
      for (const [secondary, majors] of Object.entries(secondaries)) {
        for (const majorName of Object.keys(majors)) {
          map.set(majorName, { category, secondary });
        }
      }
    }
    return map;
  });

  // --- Actions ---

  function updateStatus(text: string, color: string) {
    statusText.value = text;
    statusColor.value = color;
  }

  function addLog(msg: string) {
    logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${msg}`);
    if (logs.value.length > 50) logs.value.pop();
  }

  async function fetchMajorData() {
    if (isLoadingData.value) return;
    isLoadingData.value = true;
    try {
      const res = await getMajorsList();
      if (res?.success && res.data) {
        rawCascaderData.value = res.data;
        if (!isRunning.value) {
          updateStatus('数据就绪，请选择专业', '#3eaf18');
        }
      } else {
        throw new Error('数据格式错误');
      }
    } catch (e) {
      updateStatus('加载数据失败', '#ff4d4f');
      console.error(e);
    } finally {
      isLoadingData.value = false;
    }
  }

  function getMajorPath(majorName: string): MajorPathInfo | null {
    return majorPathMap.value.get(majorName) || null;
  }

  function prepareAutoQueue(): string[] {
    if (!rawCascaderData.value) return [];
    const queue: string[] = [];
    for (const [, secs] of Object.entries(rawCascaderData.value)) {
      for (const [, majors] of Object.entries(secs as any)) {
        for (const [name, detail] of Object.entries(majors as any)) {
          if ((detail as any).state === 1) queue.push(name);
        }
      }
    }
    return queue;
  }

  function startTask(majorName: string | null, autoMode: boolean) {
    if (isRunning.value) {
      console.warn('任务正在运行中，忽略启动请求');
      return;
    }

    stopRequested.value = false;

    if (autoMode) {
      const queue = prepareAutoQueue();
      if (queue.length === 0) {
        updateStatus('无可用任务', '#ff4d4f');
        addLog('队列生成失败：无可用专业');
        return;
      }
      autoQueue.value = queue;
      isAutoRunning.value = true;
      isRunning.value = true;
      updateStatus(`🤖 自动模式：共 ${queue.length} 个`, '#722ed1');
      addLog('自动队列生成完毕，开始执行...');
      processNextInQueue();
    } else {
      if (!majorName) {
        updateStatus('请先选择专业', '#f0a020');
        return;
      }
      isRunning.value = true;
      isAutoRunning.value = false;
      currentMajor.value = majorName;
      updateStatus(`正在启动: ${majorName}`, '#6c84ff');
      addLog(`[手动] 开始任务: ${majorName}`);
      connectAndRun(majorName);
    }
  }

  function processNextInQueue() {
    if (!isAutoRunning.value || autoQueue.value.length === 0) {
      finishAuto();
      return;
    }
    const next = autoQueue.value.shift()!;
    currentMajor.value = next;
    updateStatus(`正在: ${next} ...`, '#722ed1');
    addLog(`[自动] 开始: ${next}`);
    connectAndRun(next);
  }

  function connectAndRun(majorName: string) {
    const path = getMajorPath(majorName);
    if (!path) {
      addLog(`[错误] 找不到路径: ${majorName}`);
      if (isAutoRunning.value && !stopRequested.value) {
        setTimeout(processNextInQueue, 1000);
      } else {
        stopTask();
      }
      return;
    }

    // 清理旧连接
    if (ws) {
      ws.onclose = null; // 移除旧回调防止干扰
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      ws = null;
    }

    const taskId = `task_${Date.now()}`;
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    // ⚠️ 请确认后端地址，建议放入 import.meta.env.VITE_WS_HOST
    const host = 'localhost:8090';
    const wsUrl = `${protocol}//${host}/ws/task/${taskId}`;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        addLog('[WS] 连接成功，发送指令...');
        ws?.send(JSON.stringify({
          action: 'start',
          type: 'major',
          subject: path.category,
          secondary_subject: path.secondary,
          major: majorName
        }));
      };

      ws.onmessage = (event) => {
        try {
          const res = JSON.parse(event.data);
          if (!res.success) {
            const errMsg = res.message || '操作失败';
            addLog(`[错误] ${majorName}: ${errMsg}`);
            if (isAutoRunning.value) {
              setTimeout(processNextInQueue, 1000);
            } else {
              stopTask();
            }
            return;
          }

          const data = res.data;
          if (!data) return;

          if (res.message === 'progress_update') {
            progress.value = {
              type: data.type || 0,
              currentJob: data.current_job || '--',
              currentPage: data.current_page || 0,
              currentCount: data.current_count || 0,
              targetCount: data.target_count || 0
            };

            if (progress.value.type === 1) {
              // 更新进度文本
              const txt = isAutoRunning.value
                ? `[剩${autoQueue.value.length}] ${progress.value.currentJob} (${progress.value.currentCount}/${progress.value.targetCount})`
                : `${progress.value.currentJob} (${progress.value.currentCount}/${progress.value.targetCount})`;
              updateStatus(txt, '#6c84ff');
            } else if (progress.value.type === 2) {
              // ✅ 任务完成
              addLog(`[完成] ${majorName}`);
              updateStatus('任务已完成', '#52c41a'); // 立即更新 UI 提示
              if (isAutoRunning.value && !stopRequested.value) {
                setTimeout(processNextInQueue, AUTO_TASK_DELAY);
              } else {
                finishTask();
              }
            } else {
              addLog(`[启动] ${majorName}`);
            }
          }
        } catch (e) {
          console.error('消息解析错误:', e, event.data);
        }
      };

      ws.onerror = (err) => {
        console.error('WS Error:', err);
        addLog('[WS] 连接错误');
        if (isAutoRunning.value) {
          setTimeout(processNextInQueue, 2000);
        } else {
          stopTask();
        }
      };

      // ✅ 关键修复：防御性 onclose
      ws.onclose = () => {
        console.log('WS 连接关闭事件触发');
        // 如果此时 isRunning 已经是 false，说明是正常结束（finishTask 中关闭的），直接忽略
        if (!isRunning.value) {
          console.log('-> 任务已结束，忽略 onclose');
          return;
        }

        // 如果 isRunning 还是 true，说明是意外断开
        console.warn('-> 任务运行中连接意外断开');
        addLog('[异常] 连接意外断开');

        if (isAutoRunning.value) {
          setTimeout(processNextInQueue, 2000);
        } else {
          // 手动模式下，意外断开视为停止
          stopTask();
        }
      };

    } catch (e) {
      console.error('WS 初始化失败:', e);
      addLog('WS 初始化失败');
      if (isAutoRunning.value) setTimeout(processNextInQueue, 2000);
      else stopTask();
    }
  }

  function stopTask() {
    console.log('🛑 执行停止任务');
    stopRequested.value = true;
    if (ws) {
      try {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'stop' }));
        }
      } catch (e) { /* ignore */ }
    }
    updateStatus('本轮爬取结束后停止', '#ff9d4d');
    addLog('正在停止');
  }



  function finishTask() {
    console.log('🏁 执行手动任务完成清理');
    isRunning.value = false;
    isAutoRunning.value = false;
    currentMajor.value = null;
    stopRequested.value = false;

    progress.value = { type: 0, currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 };

    logs.value = []

    // 安全关闭 WS
    if (ws) {
      ws.onclose = null; // 防止 onclose 再次触发逻辑
      ws.close();
      ws = null;
    }

    // 刷新数据以更新专业状态
    fetchMajorData();
  }

  function finishAuto() {
    console.log('🏁 执行自动任务完成清理');
    isAutoRunning.value = false;
    isRunning.value = false;
    currentMajor.value = null;
    autoQueue.value = [];

    progress.value = { type: 0, currentJob: '--', currentPage: 0, currentCount: 0, targetCount: 0 };

    updateStatus('🎉 全部完成', '#52c41a');
    addLog('所有自动任务完成');

    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }

    fetchMajorData();
  }

  function cleanup() {
    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    isRunning.value = false;
    isAutoRunning.value = false;
  }

  // --- Return ---
  return {
    // State
    rawCascaderData,
    isLoadingData,
    isRunning,
    isAutoRunning,
    currentMajor,
    autoQueue,
    progress,
    logs,
    statusText,
    statusColor,

    // Getters (必须导出)
    percent,
    cascaderOptions,
    getMajorPath,

    // Setters
    addLog,

    // Actions
    fetchMajorData,
    startTask,
    stopTask,
    cleanup,
    finishTask,
    finishAuto
  };
});