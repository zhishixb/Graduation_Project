<template>
  <n-message-provider>
    <div class="app-container" style="width: 100%">
      <div class="fixed-content-wrapper">
        <RouterView />
      </div>
    </div>
  </n-message-provider>
</template>

<script setup lang="ts">
import { NMessageProvider } from 'naive-ui'
</script>

<style scoped>

.app-container {
  width: 100%;
  height: 100vh;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
}

.fixed-content-wrapper {
  width: 1110px;
  height: 600px;
  flex-shrink: 0;
  flex-grow: 0; /* 也不要让它自动变大 */
  background-color: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  overflow: hidden;
}

.app-container {
  width: 100%;
  height: 100vh;
  /* overflow: auto;  <-- 如果你的内容不会超出 600px，这里其实可以改为 hidden 或者 overflow-y: auto */
  overflow-x: hidden; /* 👈 确保容器内也不横向滚动 */
  overflow-y: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
}
</style>