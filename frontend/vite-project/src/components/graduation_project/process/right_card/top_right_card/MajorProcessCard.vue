<template>
  <div class="job-process-card-container" :class="`status-${status}`">

    <!-- 1. 头部：标题 + 状态徽章 -->
    <div class="job-process-card-header">
      <div class="job-process-card-title-wrapper">
        <div class="job-process-card-title">{{ cardTitle }}</div>
        <!-- 状态徽章 -->
        <n-tag
          v-if="status !== 'idle'"
          :type="badgeType"
          size="small"
          round
          class="status-badge"
        >
          <template #icon>
            <n-icon v-if="status === 'success'"><CheckmarkCircleOutline /></n-icon>
            <n-icon v-else-if="status === 'warning'"><TimeOutline /></n-icon>
            <n-icon v-else-if="status === 'loading'"><SyncOutline /></n-icon>
          </template>
          {{ badgeText }}
        </n-tag>
      </div>

      <n-button
        circle
        size="small"
        :loading="isLoadingData"
        @click="openDrawer"
        class="job-process-action-btn"
        type="info"
        strong
        secondary
      >
        <template #icon>
          <n-icon><AddCircleOutline /></n-icon>
        </template>
      </n-button>
    </div>

    <!-- 2. 中间：详细统计信息 -->
    <div class="job-process-stats">
    </div>

    <!-- 3. 底部：操作按钮 -->
    <div class="job-process-footer">
      <n-button
        size="tiny"
        :type="btnType"
        :loading="isRunning"
        :disabled="isRunning"
        @click="handleAction"
        class="job-process-start-btn"
        secondary
        round
        strong
      >
        <template #icon>
          <n-icon v-if="isCompleted"><RefreshOutline /></n-icon>
          <n-icon v-else><PlayOutline /></n-icon>
        </template>
        {{ btnText }}
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  AddCircleOutline, CheckmarkCircleOutline, TimeOutline,
  SyncOutline, RefreshOutline, PlayOutline
} from "@vicons/ionicons5";
import { useMessage } from 'naive-ui';
// 假设你有这两个 API 函数
import { cleanMajors, checkMajorStatus } from "@/apis/process";

const message = useMessage();


const status = ref<'idle' | 'loading' | 'success' | 'warning' | 'error'>('idle');
const isLoadingData = ref(false); // 用于右上角按钮的 loading

// --- 计算属性 ---
const isCompleted = computed(() => status.value === 'success');
const isRunning = computed(() => status.value === 'loading');
const cardTitle = "专业数据清洗";

// 徽章逻辑
const badgeType = computed(() => {
  if (status.value === 'success') return 'success';
  if (status.value === 'warning') return 'warning';
  if (status.value === 'error') return 'error';
  if (status.value === 'loading') return 'info';
  return 'default';
});

const badgeText = computed(() => {
  if (status.value === 'success') return '已完成';
  if (status.value === 'warning') return '待处理';
  if (status.value === 'loading') return '执行中';
  if (status.value === 'error') return '异常';
  return '';
});

// 按钮逻辑
const btnType = computed(() => {
  if (status.value === 'error') return 'error';
  if (status.value === 'success') return 'success'; // 完成后显示绿色，提示可重跑
  return 'info';
});

const btnText = computed(() => {
  if (status.value === 'loading') return '清洗中...';
  if (status.value === 'success') return '重新运行';
  if (status.value === 'warning') return '继续清洗';
  if (status.value === 'error') return '重试';
  return '开始';
});

// --- 方法 ---

// 1. 检查状态 (初始化调用)
const fetchStatus = async () => {
  try {
    status.value = 'idle'; // 重置为中间态，防止闪烁
    const res = await checkMajorStatus(); // 调用后端 is_majors_cleand

    if (res.success) {
      status.value = 'success';
    } else {
      status.value = 'error';
      message.error(res.message);
    }
  } catch (e: any) {
    status.value = 'error';
    message.error(`状态检查失败：${e.message}`);
  }
};

// 2. 执行动作 (开始/重试)
const handleAction = async () => {
  if (isRunning.value) return;
  status.value = 'loading';

  try {
    const res = await cleanMajors();

    if (res.success) {
      message.success(res.message);
      // 任务完成后，立即刷新状态以获取最新统计
      await fetchStatus();
    } else {
      status.value = 'error';
      message.error(res.message);
    }
  } catch (e: any) {
    status.value = 'error';
    message.error(`执行失败：${e.message}`);
  }
};

const openDrawer = () => {
  // 打开配置抽屉
  console.log("Open config drawer");
};

// 生命周期：挂载时自动检查
onMounted(() => {
  fetchStatus();
});
</script>

<style scoped>
.job-process-card-container {
  width: 165px;
  height: 150px;
  display: flex;
  flex-direction: column;
  padding: 12px;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid #eee;
}

/* 状态样式修饰 */
.job-process-card-container.status-success {
  border-color: #18a058;
  background-color: #f0f9f4;
}
.job-process-card-container.status-warning {
  border-color: #f0a020;
  background-color: #fffbe6;
}
.job-process-card-container.status-error {
  border-color: #d03050;
  background-color: #fff0f1;
}
.job-process-card-container.status-loading {
  border-color: #2080f0;
  background-color: #f0faff;
}

.job-process-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start; /* 顶部对齐 */
  width: 100%;
  margin-bottom: 8px;
}

.job-process-card-title-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 110px;
}

.job-process-card-title {
  font-weight: bold;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  font-size: 10px;
  transform: scale(0.9);
  transform-origin: left center;
  height: 18px;
}

.job-process-action-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
}

/* 中间统计区域 */
.job-process-stats {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  padding: 4px 0;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  opacity: 0.8;
}

.stat-value {
  font-weight: bold;
  font-family: monospace; /* 数字等宽显示更整齐 */
}

.success-text { color: #18a058; }
.warning-text { color: #f0a020; }

.stat-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #2080f0;
}

.job-process-footer {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: auto;
}

.job-process-start-btn {
  width: 100%;
  font-size: 12px;
  height: 28px;
}

.job-process-start-btn{
  width: 105px;
  margin-left: -33px;
}
</style>