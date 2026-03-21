<template>
  <div class="job-process-card-container">
    <div class="job-process-card-header">
      <div class="job-process-card-title">专业数据清洗</div>
      <n-button
          circle
          size="small"
          :loading="isLoadingData"
          :disabled="isRunning"
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
  </div>
</template>

<script setup lang="ts">

import {AddCircleOutline} from "@vicons/ionicons5";
</script>

<style scoped>
.job-process-card-container {
  width: 165px;
  height: 150px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background-color: #fefefe;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  position: relative;
  overflow: hidden; /* 必须保留，用于裁剪抽屉 */
}

.job-process-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  z-index: 1;
}

.job-process-card-title {
  font-weight: bold;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 110px;
}

.job-process-action-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  z-index: 1;
}
</style>