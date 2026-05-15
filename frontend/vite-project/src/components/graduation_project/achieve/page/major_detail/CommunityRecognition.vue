<template>
  <div class="community-card">
    <h3 class="card-title">专业社区认可情况</h3>
    <div class="content">
      <!-- 专业认同度 -->
      <div class="row">
        <span class="label">专业认同度</span>
        <n-tooltip trigger="hover">
          <template #trigger>
            <div class="bar-container">
              <div class="bar-fill" :style="{ width: (data.positive_ratio * 100) + '%' }"></div>
              <span class="bar-text">{{ (data.positive_ratio * 100).toFixed(1) }}%</span>
            </div>
          </template>
          <span>正面评论占比，反映社区对该专业的整体认可程度</span>
        </n-tooltip>
      </div>

      <!-- 观点认可度 -->
      <div class="row">
        <span class="label">观点认可度</span>
        <n-tooltip trigger="hover">
          <template #trigger>
            <span class="value">{{ data.avg_likes.toFixed(2) }}</span>
          </template>
          <span>平均点赞数，反映评论观点获得的认同程度</span>
        </n-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NTooltip } from 'naive-ui'

interface SentimentData {
  major: string
  positive_ratio: number
  avg_likes: number
  total_likes: number
  record_count: number
  weighted_pos_total: number
  weighted_neg_total: number
}

defineProps<{
  data: SentimentData
}>()
</script>

<style scoped>
.community-card {
  width: 320px;
  height: 200px;
  background: #ffffff01;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  padding: 16px 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.card-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 20px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.label {
  width: 80px;
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
  flex-shrink: 0;
}

/* 进度条容器 */
.bar-container {
  position: relative;
  flex: 1;
  height: 22px;
  background: #f0f0f5;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  cursor: help;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #69b1ff, #1677ff);
  border-radius: 6px;
  transition: width 0.4s ease;
}

.bar-text {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  font-weight: 600;
  color: #1a1a2e;
  white-space: nowrap;
}

.value {
  font-size: 18px;
  font-weight: 700;
  color: #1677ff;
  cursor: help;
}
</style>