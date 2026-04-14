<!-- MatchScores.vue -->
<template>
  <div class="match-scores">
    <h3>{{ title }}</h3>
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
        <span class="bar-label">{{ labels[idx] }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const title = '匹配分数';
const scores = ref([0.65, 0.82, 0.43, 0.91, 0.57, 0.73, 0.38]);
const labels = ['维度A', '维度B', '维度C', '维度D', '维度E', '维度F', '维度G'];

// 不同进度条的颜色（渐变）
const barColors = [
  'linear-gradient(180deg, #6C5CE7, #a29bfe)',
  'linear-gradient(180deg, #0984E3, #74B9FF)',
  'linear-gradient(180deg, #00B894, #55EFC4)',
  'linear-gradient(180deg, #FDCB6E, #FFEAA7)',
  'linear-gradient(180deg, #E17055, #FF7675)',
  'linear-gradient(180deg, #D63031, #FF7675)',
  'linear-gradient(180deg, #6C5CE7, #a29bfe)',
];
</script>

<style scoped>
.match-scores {
  background: white;
  border-radius: 20px;
  padding: 12px 12px;
  width: 100%;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
}

.match-scores h3 {
  font-size: 14px;
  margin-bottom: 12px;
  color: #333;
  font-weight: 600;
  text-align: center;
}

.bars-container {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 6px;           /* 进一步减小间距 */
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 28px;        /* 进度条宽度进一步缩减 */
}

.bar-wrapper {
  width: 7px;
  height: 50px;       /* 略微再降低高度 */
  background: #f0f0f5;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  overflow: hidden;
}

.bar {
  width: 7px;
  border-radius: 8px 8px 0 0;
  transition: height 0.3s ease;
}

.score-value {
  font-size: 9px;
  font-weight: 600;
  color: #555;
}

.bar-label {
  font-size: 9px;
  color: #888;
  /* 文字倾斜（旋转）以节省水平空间 */
  transform: rotate(-30deg);
  display: inline-block;
  white-space: nowrap;
  margin-top: 4px;
  /* 调整偏移，避免旋转后超出边界 */
  transform-origin: center top;
}
</style>