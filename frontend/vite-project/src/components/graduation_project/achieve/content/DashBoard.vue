<template>
  <div class="dashboard-content">
    <div class="left-column">
      <div class="title-card">
        <span class="title-text">Career Bridge</span>
        <span class="title-line"></span>
      </div>
      <PositionSearch style="margin-top: 80px;" :reveal="true" />
      <MajorSearch :reveal="true" />
      <MatchScores :reveal="true" />
      <CompareCard :reveal="true"></CompareCard>
    </div>
    <div class="middle-column"></div>
    <div class="right-column">
      <HotMajors :reveal="true" />
    </div>
  </div>
</template>

<script setup lang="ts">
import PositionSearch from '@/components/graduation_project/achieve/page/dash_board/PositionSearch.vue';
import MajorSearch from '@/components/graduation_project/achieve/page/dash_board/MajorSearch.vue';
import MatchScores from '@/components/graduation_project/achieve/page/dash_board/MatchScores.vue';
import CompareCard from '@/components/graduation_project/achieve/page/dash_board/CompareCard.vue';
import HotMajors from '@/components/graduation_project/achieve/page/dash_board/HotMajors.vue';
</script>

<style scoped>  
.dashboard-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
  z-index: 10;
}

.left-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 30%;
  height: 100%;
  min-height: 0;
  pointer-events: auto;
}

.middle-column {
  width: 45%;
  height: 100%;
}

.right-column {
  width: 25%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-top: 20px;
  pointer-events: auto;
}

/* 无背景卡片，宽度自适应内容 */
.title-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0;
  max-width: fit-content;
  box-shadow: none;
}

/* 浅灰→中灰渐变文字 */
.title-text {
  font-size: 25px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, #b0b0b0, #6e6e6e);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  display: inline-block;
}

/* 装饰线同样使用该渐变 */
.title-line {
  display: block;
  width: 40px;
  height: 3px;
  background: linear-gradient(90deg, #b0b0b0, #6e6e6e);
  border-radius: 2px;
}
</style>