<template>
  <div class="info-content">
    <h1>{{ majorName }}</h1>

    <div class="scroll-content">
      <h3>专业介绍</h3>
      <div class="text-block">{{ majorData.description }}</div>

      <h3>学习课程</h3>
      <div class="text-block">{{ majorData.main_courses }}</div>

      <h3>培养方向</h3>
      <div class="text-block">{{ majorData.training_direction }}</div>

      <h3>发展方向</h3>
      <div class="text-block">{{ majorData.employment_direction }}</div>

      <h3>社区评价</h3>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  majorName: {
    type: String,
    required: true
  },
  majorData: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
/* 根容器：纵向 flex，撑满父级高度，标题固定，下方滚动 */
.info-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 28px 24px 0 24px;   /* 顶部和左右内边距，底部留给滚动区 */
  color: #2c3e50;
  box-sizing: border-box;
}

h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: #1a1a2e;
  line-height: 1.4;
  flex-shrink: 0;            /* 标题不参与滚动 */
}

/* 可滚动内容区 */
.scroll-content {
  flex: 1;
  overflow-y: auto;          /* 内容超出时垂直滚动 */
  padding-bottom: 28px;      /* 底部内边距，代替原来的底部 padding */
  box-sizing: border-box;

  /* 隐藏滚动条（跨浏览器） */
  -ms-overflow-style: none;  /* IE/Edge */
  scrollbar-width: none;     /* Firefox */
}

/* WebKit 浏览器隐藏滚动条 */
.scroll-content::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 8px 0;
  color: #3a4a5c;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  padding-bottom: 4px;
}

.text-block {
  font-size: 14px;
  line-height: 1.8;
  color: #4b5563;
  margin-bottom: 8px;
}
</style>