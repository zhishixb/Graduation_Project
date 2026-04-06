<template>
  <div class="search-spider-card" :class="`status-${store.isRunning ? 'running' : 'idle'}`" id="spider-job-51job-card-container">
    <div class="start-card-left">
      <div class="search-spider-card-title">
        {{ store.isAutoRunning ? '🤖 自动批量爬取' : '51Job岗位爬取' }}
      </div>

      <div class="search-spider-card-state">
        <MarqueeText :text="store.contentText" :speed="3.5" :color="store.contentColor" />
      </div>

      <div style="height: 30px">
        <transition name="fade">
          <div v-show="store.logs.length > 0" class="signal-log-area">
            <div class="log-entry">{{ store.logs[0] }}</div>
          </div>
        </transition>
      </div>

      <div class="start-card-info-placeholder">
        <n-button
          strong
          secondary
          :type="store.isRunning ? 'info' : 'error'"
          :loading="store.isRunning"
          style="border-radius: 30px; height: 30px; font-size: 10px; width: 100%; margin-top: 4px"
          @click="handleStart"
        >
          {{ store.isRunning ? '运行中' : '开始爬取' }}
        </n-button>
      </div>
    </div>

    <div class="start-card-right">
      <!-- 手动模式：级联选择器 -->
      <n-cascader
        v-if="!store.isRunning && !store.isAutoRunning"
        v-model:value="store.selectedPosition"
        :options="store.cascaderOptions"
        placeholder="选职位"
        size="small"
        clearable
        :disabled="store.isLoadingData"
        filterable
        :show-path="true"
        style="width: 100%; margin-top: -10px"
        placement="bottom-end"
        @update:value="store.selectPosition"
      />

      <!-- 自动模式复选框 -->
      <div v-if="!store.isRunning && !store.isAutoRunning" style="display: flex; gap: 5px; align-items: center; justify-content: flex-end">
        <n-checkbox v-model:checked="useAutoMode" size="small" style="font-size: 10px; transform: scale(0.9)">
          自动
        </n-checkbox>
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-icon size="14" style="color: #999; cursor: help">
              <AlertCircleOutline />
            </n-icon>
          </template>
          开启后将按顺序爬取所有状态为“待爬取”的职位
        </n-tooltip>
      </div>

      <div v-if="store.isLoadingData && !store.isRunning" class="loading-tip">加载数据中...</div>

      <!-- 运行状态显示 -->
      <transition name="fade">
        <div class="right-running-status" v-if="store.isRunning">
          <n-progress
            :style="{ width: '40px', marginTop: '-10px', '--n-font-size-circle': '10px', '--n-icon-size-circle': '36px' }"
            type="circle"
            :stroke-width="15"
            :percentage="store.percent"
            processing
          />
          <div style="font-size: 9px; text-align: center">
            当前:<br />{{ store.currentPosition || '--' }}
            <span v-if="store.isAutoRunning && store.autoQueue.length > 0">
              <br />剩余:{{ store.autoQueue.length }}
            </span>
          </div>
          <n-button
            strong
            secondary
            type="warning"
            size="small"
            style="width: 100%; height: 30px; font-size: 10px; border-radius: 30px; margin-bottom: 5px"
            @click="handleStop"
          >
            暂停
          </n-button>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useMessage } from 'naive-ui'
import { AlertCircleOutline } from '@vicons/ionicons5'
import MarqueeText from '@/components/public/MarqueeText.vue'
import { useJobByPositionStore } from '@/stores/spider/job_by_position'

const message = useMessage()
const store = useJobByPositionStore()
const useAutoMode = ref(false)

const handleStart = () => {
  const position = store.selectedPosition
  if (!useAutoMode.value && !position) {
    message.warning('请先选择一个职位或开启自动模式')
    return
  }
  store.startTask(
    position,
    useAutoMode.value,
    (msg, type = 'info') => {
      if (type === 'success') message.success(msg)
      else if (type === 'error') message.error(msg)
      else if (type === 'warning') message.warning(msg)
      else message.info(msg)
    },
    (errMsg) => message.error(errMsg)
  )
}

const handleStop = () => {
  store.stopTask((msg, type = 'warning') => {
    if (type === 'warning') message.warning(msg)
    else message.info(msg)
  })
}

onMounted(() => {
  store.fetchCountJobs().catch(() => {
    message.error('加载数据失败')
  })
})

onBeforeUnmount(() => {
  store.dispose()
})
</script>

<style scoped>
/* 样式基本保持原样，可添加运行状态边框颜色 */
.search-spider-card {
  width: 230px;
  height: 150px;
  display: flex;
  gap: 12px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
}
.search-spider-card.status-running {
  border-color: #2080f0;
  background-color: #f8fcff;
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
  gap: 12px;
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
.right-running-status {
  display: flex;
  gap: 5px;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
:deep(.n-cascader) {
  width: 100%;
}
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
:deep(.n-cascader__label) {
  padding-left: 6px;
  color: #333;
}
:deep(.n-cascader-menu) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  border-radius: 6px !important;
  border: 1px solid #eee !important;
  font-size: 12px;
}
</style>