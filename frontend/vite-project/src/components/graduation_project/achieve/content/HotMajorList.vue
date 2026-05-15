<template>
  <div class="hot-major-page">
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" class="title-icon">
          <ThermometerOutline />
        </n-icon>
        热门专业排行
      </h1>
    </div>
    <div class="list-container">
      <div v-if="majors.length === 0" class="empty-tip">加载中...</div>
      <div
        v-for="(item, idx) in majors"
        :key="idx"
        class="major-row"
        @click="handleClick(item.name)"
      >
        <span class="row-rank" :style="{ background: rankColor(idx) }">{{ idx + 1 }}</span>
        <span class="row-name">{{ item.name }}</span>
        <span class="row-heat">{{ formatHeat(item.heat_value) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NIcon } from 'naive-ui'
import { ThermometerOutline } from '@vicons/ionicons5'
import { useDataStore } from '@/stores/achieve/dataStore.ts'
import { getHotMajors } from '@/apis/business.ts'

const store = useDataStore()

interface MajorHeatItem {
  name: string
  heat_value: number
}

const majors = ref<MajorHeatItem[]>([])

// 排名颜色数组（可自定义，共30个色，这里给出前10个常用色，后面循环）
const rankColors = [
  '#FF6B6B', '#FF8E53', '#FFD93D', '#6BCB77', '#4D96FF',
  '#9B59B6', '#34495E', '#E67E22', '#1ABC9C', '#F368E0',
  '#FF4757', '#FF6348', '#FFC048', '#2ED573', '#1E90FF',
  '#A29BFE', '#6C5CE7', '#00CEC9', '#55EFC4', '#FAB1A0',
  '#FF7675', '#FDCB6E', '#00B894', '#0984E3', '#6C5CE7',
  '#E056A0', '#0ABDE3', '#10AC84', '#F368E0', '#FF9FF3'
]

const formatHeat = (value: number): string => {
  if (value >= 10000) {
    return (value / 10000).toFixed(1).replace(/\.0$/, '') + '万'
  }
  return value.toString()
}

const rankColor = (index: number): string => {
  return rankColors[index % rankColors.length]
}

const handleClick = (name: string) => {
  store.selectMajorName(name)
  store.isLoading = true
  setTimeout(() => {
    store.turnToPage('majorDetail')
  }, 400)
}

onMounted(async () => {
  try {
    const res = await getHotMajors(30)
    if (res.success && Array.isArray(res.data?.majors)) {
      majors.value = res.data.majors
    }
  } catch (e) {
    console.error('获取热门专业失败', e)
  }
  setTimeout(() => store.isLoading = false, 400)
})
</script>

<style scoped>
.hot-major-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f9f9fc;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;           /* 防止 body 滚动 */
}

.page-header {
  padding: 24px 32px 16px;
  flex-shrink: 0;
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
  display: flex;
  align-items: center;
}

.title-icon {
  margin-right: 8px;
}

.list-container {
  flex: 1;
  min-height: 0;              /* 关键：允许 flex 子元素收缩以显示滚动条 */
  overflow-y: auto;
  padding: 0 32px 24px;
}

.empty-tip {
  text-align: center;
  color: #999;
  margin-top: 60px;
  font-size: 15px;
}

.major-row {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  margin-bottom: 4px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
}

.major-row:hover {
  background: #f0f2ff;
  box-shadow: 0 4px 12px rgba(108, 92, 231, 0.12);
}

.row-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-radius: 6px;          /* 圆角正方形 */
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  margin-right: 16px;
}

.row-name {
  flex: 1;
  font-size: 16px;
  font-weight: 500;
  color: #2c3e50;
}

.row-heat {
  font-size: 14px;
  font-weight: 600;
  color: #6C5CE7;
  margin-left: 16px;
}

/* 滚动条美化 */
.list-container::-webkit-scrollbar {
  width: 6px;
}
.list-container::-webkit-scrollbar-track {
  background: transparent;
}
.list-container::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 3px;
}
</style>