<template>
  <div class="search-spider-card" :class="`status-${store.isLoadingData ? 'loading' : 'idle'}`" id="spider-major-51job-card-container">
    <!-- 左侧：标题与状态 -->
    <div class="start-card-left">
      <div class="search-spider-card-title">
        {{ store.isAutoRunning ? '自动批量爬取' : '51Job专业爬取' }}
      </div>

      <div class="search-spider-card-state">
        <MarqueeText :text="store.statusText" :speed="3.5" :color="store.statusColor" />
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
          :type="store.isRunning ? 'info' : 'warning'"
          :loading="store.isRunning"
          style="border-radius: 30px; height: 30px; font-size: 10px; width: 100%; margin-top: 4px"
          @click="handleStartClick"
        >
          {{ store.isRunning ? '运行中' : '开始爬取' }}
        </n-button>
      </div>
    </div>

    <!-- 右侧：选择器与控制区 -->
    <div class="start-card-right">
      <!-- 级联选择器 -->
      <n-cascader
        v-model:value="selectedMajorName"
        v-model:show="cascaderShow"
        :options="cascaderOptions"
        placeholder="选专业"
        size="small"
        clearable
        :disabled="store.isLoadingData || store.isRunning || store.isAutoRunning"
        :filterable="true"
        :show-path="true"
        :emit-path="false"
        style="width: 100%; margin-top: -10px"
        to="#spider-major-51job-card-container"
        placement="bottom-end"
        strategy="fixed"
        @update:value="handleMajorChange"
        v-if="!store.isRunning && !store.isAutoRunning"
      />

      <!-- 自动化 Checkbox -->
      <div v-if="!store.isRunning && !store.isAutoRunning" style="display: flex; gap: 5px; align-items: center;">
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

      <div v-if="store.isLoadingData && !store.isAutoRunning" class="loading-tip">加载数据中...</div>

      <!-- 运行状态 -->
      <transition name="fade">
        <div class="right-running-status" v-if="store.isRunning">
          <n-progress
              :style="{ width: '40px', marginTop: '-10px', '--n-font-size-circle': '10px', '--n-icon-size-circle': '36px' }"
              type="circle"
              :stroke-width="15"
              :percentage="store.percent"
              processing
          />
          <div style="font-size: 9px; text-align: center;">正在爬取:<br/>{{ store.currentMajor || '--' }}</div>
          <n-button
            strong
            secondary
            type="warning"
            size="small"
            style="width: 100%; height: 30px; font-size: 10px; border-radius: 30px; margin-bottom: 5px"
            @click="store.stopTask"
          >
            暂停
          </n-button>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useSpiderStore } from '@/stores/spider/job_by_major';
import MarqueeText from "@/components/public/MarqueeText.vue";
import { AlertCircleOutline } from "@vicons/ionicons5";

const store = useSpiderStore();
const selectedMajorName = ref<string | null>(null);
const useAutoMode = ref(false);

// ✅ 新增：控制级联选择器的显示/隐藏
const cascaderShow = ref(false);

const cascaderOptions = computed(() => store.cascaderOptions);

const handleMajorChange = (val: string | null) => {
  selectedMajorName.value = val;

  if (val) {
    const path = store.getMajorPath(val);
    if (path) {
      store.statusText = `目标：${path.category} - ${path.secondary} - ${val}`;
      store.statusColor = '#6cb1ff';
      store.addLog(`已锁定：${val}`);

      // ✅ 关键：选中后，延迟关闭下拉菜单
      // 使用 nextTick 或 setTimeout 确保 UI 先渲染选中的值，再关闭
      setTimeout(() => {
        cascaderShow.value = false;
      }, 150);
    }
  } else {
    // 如果清空了值
    if (!store.isRunning) {
      store.statusText = '等待选择...';
      store.statusColor = '#969696';
    }
    // 清空时也关闭菜单
    cascaderShow.value = false;
  }
};

const handleStartClick = () => {
  // 点击开始时，如果菜单还开着，先关掉
  cascaderShow.value = false;
  store.startTask(selectedMajorName.value, useAutoMode.value);
};

onMounted(() => {
  store.fetchMajorData();
});
</script>

<style scoped>
.search-spider-card {
  width: 230px;
  height: 150px;
  display: flex;
  gap: 12px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  box-sizing: border-box;
  position: relative;
  transition: all 0.3s ease;
  border: 1px solid #f0a020; /* 橙色边框 */
  z-index: 100;
  background-color: #fefefe;
}


.search-spider-card.status-loading {
  border-color: #2080f0;
}

.search-spider-card.status-error {
  border-color: #d03050;
}

.search-spider-card.status-success {
  border-color: #18a058;
}

.search-spider-card.status-warning {
  border-color: #f0a020;
}

.search-spider-card.status-idle {
  border-color: #e0e0e0;
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