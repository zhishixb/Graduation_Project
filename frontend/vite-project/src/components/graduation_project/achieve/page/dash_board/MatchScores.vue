<template>
  <div class="match-scores" :class="{ 'reveal-active': showReveal }">
    <!-- 包裹实际内容的层（用于淡入） -->
    <div class="content-wrapper" :class="{ 'fade-in': showReveal }">
      <h3 v-if="showTitle">{{ title }}</h3>
      <h1></h1>
      <div class="bars-container">
        <div v-for="(score, idx) in scores" :key="idx" class="bar-item">
          <div class="bar-wrapper">
            <div
              class="bar"
              :style="{
                height: score * 100 + '%',
                background: barColors[idx]
              }"
            ></div>
          </div>
          <span class="score-value">{{ score.toFixed(2) }}</span>
        </div>
      </div>
      <!-- 新增匹配列表 -->
      <div class="score-list">
        <div v-for="(score, idx) in scores" :key="'list-' + idx" class="list-item">
          <span class="list-label">{{ labels[idx] }}</span>
          <span class="list-score">{{ score.toFixed(2) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue';

const props = withDefaults(defineProps<{
  showTitle?: boolean;
  reveal?: boolean;
}>(), {
  showTitle: true,
  reveal: false,
});

const title = '匹配分数';
const scores = ref([0.65, 0.82, 0.43, 0.91, 0.57]);
const labels = ['维度A', '维度B', '维度C', '维度D', '维度E'];
const barColors = [
  'linear-gradient(180deg, #6C5CE7, #a29bfe)',
  'linear-gradient(180deg, #0984E3, #74B9FF)',
  'linear-gradient(180deg, #00B894, #55EFC4)',
  'linear-gradient(180deg, #FDCB6E, #FFEAA7)',
  'linear-gradient(180deg, #E17055, #FF7675)',
];

const showReveal = ref(false);
let timer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.reveal,
  (newVal) => {
    if (timer) clearTimeout(timer);
    if (newVal) {
      timer = setTimeout(() => {
        showReveal.value = true;
      }, 20);
    } else {
      showReveal.value = false;
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer);
});
</script>

<style scoped>
/* ---------- 容器 ---------- */
.match-scores {
  position: relative;
  background: transparent;
  border-radius: 20px;
  padding: 10px 8px;       /* 内边距由 12px 12px 缩小 */
  width: 60%;
  overflow: hidden;
}

/* ---------- 内容包裹层（淡入动画） ---------- */
.content-wrapper {
  position: relative;
  z-index: 1;
  opacity: 0;
  transition: opacity 0.6s ease;
}

.fade-in {
  opacity: 1;
  transition-delay: 0.8s;
}

/* ---------- 标题左对齐 ---------- */
.match-scores h3 {
  font-size: 11px;
  margin-bottom: 10px;     /* 下边距从 12px 缩小到 10px */
  color: #666;
  font-weight: 600;
  text-align: left;
}

/* ---------- 柱状图容器 ---------- */
.bars-container {
  display: flex;
  justify-content: flex-start;
  align-items: flex-end;
  gap: 2px;                /* 柱间距从 3px 缩小到 2px */
  margin-bottom: 14px;     /* 与列表间距从 16px 缩小到 14px */
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 24px;             /* 每个柱位宽度从 28px 缩小到 24px */
}

.bar-wrapper {
  width: 6px;              /* 柱子宽度从 7px 缩小到 6px */
  height: 50px;
  background: #f0f0f5;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  overflow: hidden;
}

.bar {
  width: 6px;              /* 与 bar-wrapper 保持一致 */
  border-radius: 8px 8px 0 0;
  transition: height 0.3s ease;
}

.score-value {
  font-size: 8px;          /* 数字从 9px 缩小到 8px */
  font-weight: 600;
  color: #555;
}

/* ---------- 新增匹配列表 ---------- */
.score-list {
  display: flex;
  flex-direction: column;
  gap: 4px;                /* 列表行间距从 6px 缩小到 4px */
  margin-top: 4px;
}

.list-item {
  display: flex;
  justify-content: space-between;
  padding: 2px 4px;        /* 内边距从 2px 6px 缩小 */
  font-size: 11px;         /* 字号从 12px 缩小到 11px */
  color: #333;
  background: rgba(0,0,0,0.02);
  border-radius: 4px;
}

.list-label {
  font-weight: 500;
  color: #444;
}

.list-score {
  font-weight: 600;
  color: #6C5CE7;
  min-width: 40px;
  text-align: right;
}
</style>