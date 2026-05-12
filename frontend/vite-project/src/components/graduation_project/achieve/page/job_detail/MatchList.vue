<template>
  <div class="similarity-card">
    <!-- 如果没有数据时的兜底展示 -->
    <div v-if="!sortedData || sortedData.length === 0" class="empty-tip">暂无匹配数据</div>

    <div v-else>
      <!-- 竖条图表部分（仅包含条形，无文字/分数） -->
      <div class="chart-container">
        <div
          v-for="(item, index) in sortedData"
          :key="index"
          class="bar-item"
        >
          <div
            class="bar-wrapper"
            :style="{ height: barHeights[index] + 'px' }"
          >
            <!-- 未匹配部分（上方，更显眼的颜色） -->
            <div
              class="bar-segment bar-unmatched"
              :style="{ height: ((1 - item.similarity) * (barHeights[index] - 3)) + 'px' }"
            ></div>
            <!-- 已匹配部分（下方，蓝色渐变） -->
            <div
              class="bar-segment bar-matched"
              :style="{ height: (item.similarity * (barHeights[index] - 3)) + 'px' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- 纵向列表：显示职位名称与匹配度 -->
      <div class="list-container">
        <div
          v-for="(item, index) in sortedData"
          :key="'list-' + index"
          class="list-item"
        >
          <span class="item-name" :title="item.major_name">{{ item.major_name }}</span>
          <span class="item-score">{{ (item.similarity * 100).toFixed(1) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

// 按匹配度从高到低排序
const sortedData = computed(() => {
  if (!props.data || props.data.length === 0) return []
  return [...props.data].sort((a, b) => b.similarity - a.similarity)
})

// 为每个竖条生成 40~70px 之间的随机总高度（数据变化时会重新生成）
const barHeights = computed(() => {
  if (!sortedData.value || sortedData.value.length === 0) return []
  return sortedData.value.map(() => Math.floor(Math.random() * 31) + 40) // 40 ~ 70 整数
})
</script>

<style scoped>
/* 核心容器 */
.similarity-card {
  width: 250px;
  padding: 2px 2px;
  background: transparent;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  box-sizing: border-box;
}

.card-title {
  margin: 0 0 14px 0;
  font-size: 16px;
  color: #333;
  text-align: center;
}

.empty-tip {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 20px 0;
}

/* -------------------- 竖条图表区域 -------------------- */
.chart-container {
  display: flex;
  flex-wrap: nowrap;
  justify-content: flex-start;
  align-items: flex-end;
  gap: 3px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 14px;
}

.chart-container::-webkit-scrollbar {
  height: 4px;
}
.chart-container::-webkit-scrollbar-track {
  background: transparent;
}
.chart-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
}

/* 竖条外层容器：移除固定高度，改用内联动态高度 */
.bar-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 3px;
  width: 12px;
  border-radius: 4px;
}

.bar-segment {
  width: 6px;
  border-radius: 4px;
  transition: height 0.6s cubic-bezier(0.25, 0.8, 0.25, 1.2);
  flex-shrink: 0;
}

/* 已匹配部分：蓝色渐变 */
.bar-matched {
  background: linear-gradient(to top, #1677ff 0%, #69b1ff 100%);
  min-height: 0;
}

/* 未匹配部分：更为显眼的浅橙色，并增加一点阴影突出 */
.bar-unmatched {
  background: #ffbb96;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
  min-height: 0;
}

/* -------------------- 下方纵向列表 -------------------- */
.list-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
  padding-right: 4px;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: #e6e6e688;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.4;
}

.item-name {
  color: #333;
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-score {
  color: #1677ff;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

/* 列表滚动条美化 */
.list-container::-webkit-scrollbar {
  width: 4px;
}
.list-container::-webkit-scrollbar-track {
  background: transparent;
}
.list-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}
</style>