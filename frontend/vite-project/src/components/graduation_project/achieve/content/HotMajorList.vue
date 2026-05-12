<template>
  <div class="hot-major-list-container">
    <!-- 标题栏 -->
    <div class="list-header">
      <div class="header-left">
        <span class="header-icon">🔥</span>
        <h3 class="header-title">热门专业排行</h3>
      </div>
      <span class="header-badge">本周更新</span>
    </div>

    <!-- 列表区域（可滚动） -->
    <div class="list-scroll-area">
      <div
        v-for="(item, index) in majorList"
        :key="item.id"
        class="major-item"
        :style="{ animationDelay: `${index * 0.08}s` }"
      >
        <!-- 排名 -->
        <div class="rank-badge" :class="getRankClass(index)">
          <span v-if="index === 0">👑</span>
          <span v-else-if="index === 1">🥈</span>
          <span v-else-if="index === 2">🥉</span>
          <span v-else>{{ index + 1 }}</span>
        </div>

        <!-- 专业信息 -->
        <div class="major-info">
          <div class="major-name">{{ item.name }}</div>
          <div class="major-category">{{ item.category }}</div>
        </div>

        <!-- 热度进度条 -->
        <div class="hotness-bar-wrapper">
          <div class="hotness-bar">
            <div
              class="hotness-fill"
              :style="{ width: item.hotness + '%', background: item.color }"
            ></div>
          </div>
          <span class="hotness-value">{{ item.hotness }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface MajorItem {
  id: number
  name: string
  category: string
  hotness: number
  color: string
}

const majorList = ref<MajorItem[]>([
  { id: 1, name: '人工智能', category: '计算机科学', hotness: 98, color: '#FF6B6B' },
  { id: 2, name: '数据科学', category: '统计学', hotness: 92, color: '#4ECDC4' },
  { id: 3, name: '金融科技', category: '金融学', hotness: 87, color: '#FFD93D' },
  { id: 4, name: '新能源科学', category: '能源工程', hotness: 83, color: '#6C5CE7' },
  { id: 5, name: '生物医学工程', category: '生物工程', hotness: 79, color: '#A8E6CF' },
  { id: 6, name: '机器人工程', category: '自动化', hotness: 75, color: '#FF8B94' },
  { id: 7, name: '数字媒体艺术', category: '设计学', hotness: 71, color: '#B8A9C9' },
  { id: 8, name: '网络安全', category: '计算机科学', hotness: 68, color: '#55E6C1' },
])

function getRankClass(index: number) {
  if (index === 0) return 'rank-gold'
  if (index === 1) return 'rank-silver'
  if (index === 2) return 'rank-bronze'
  return 'rank-normal'
}
</script>

<style scoped>
/* 容器保持原尺寸 */
.hot-major-list-container {
  width: 648px;
  height: 464px;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.06);
  padding: 24px;
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 头部 */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 24px;
  line-height: 1;
}

.header-title {
  font-size: 18px;
  font-weight: 700;
  color: #2D3436;
  margin: 0;
}

.header-badge {
  background: #F0F0F5;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  color: #888;
  font-weight: 500;
}

/* 可滚动列表区域 */
.list-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: #E0E0E0 transparent;
}

.list-scroll-area::-webkit-scrollbar {
  width: 4px;
}

.list-scroll-area::-webkit-scrollbar-thumb {
  background: #E0E0E0;
  border-radius: 4px;
}

/* 单个列表项 */
.major-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: #FAFAFC;
  border-radius: 16px;
  margin-bottom: 10px;
  transition: all 0.25s cubic-bezier(0.23, 1, 0.32, 1);
  animation: fadeInUp 0.4s ease backwards;
  cursor: pointer;
}

.major-item:hover {
  background: #F0F0FF;
  transform: translateX(6px);
  box-shadow: 0 8px 20px rgba(108, 92, 231, 0.08);
}

/* 入场动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 排名徽章 */
.rank-badge {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  margin-right: 14px;
  flex-shrink: 0;
}

.rank-gold {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: white;
}

.rank-silver {
  background: linear-gradient(135deg, #C0C0C0, #A9A9A9);
  color: white;
}

.rank-bronze {
  background: linear-gradient(135deg, #CD7F32, #B87333);
  color: white;
}

.rank-normal {
  background: #E4E6F0;
  color: #666;
  font-size: 14px;
}

/* 专业信息 */
.major-info {
  flex: 1;
  min-width: 0;
}

.major-name {
  font-size: 15px;
  font-weight: 600;
  color: #2D3436;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.major-category {
  font-size: 12px;
  color: #999;
}

/* 热度条 */
.hotness-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 140px;
  flex-shrink: 0;
}

.hotness-bar {
  flex: 1;
  height: 6px;
  background: #E8ECF1;
  border-radius: 3px;
  overflow: hidden;
}

.hotness-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.hotness-value {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  min-width: 34px;
  text-align: right;
}
</style>