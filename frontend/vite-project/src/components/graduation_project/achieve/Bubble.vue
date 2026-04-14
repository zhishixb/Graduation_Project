<!-- components/Bubble.vue -->
<template>
  <div
    class="bubble"
    :class="colorTheme"
    :style="{
      top: position.top,
      right: position.right,
      width: size.width,
      height: size.height,
    }"
  >
    <span>{{ title }}</span>
    <!-- 下层内容：优先显示图标，否则显示文字 -->
    <component :is="icon" v-if="icon" class="bubble-icon" />
    <b v-else>{{ value }}</b>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue';

interface Props {
  color?: 'purple' | 'blue' | 'orange';
  top?: string;
  right?: string;
  width?: string;
  height?: string;
  title?: string;
  // 支持传入图标组件（来自 @vicons/ionicons5 或其他）
  icon?: Component;
  // 当没有图标时显示的文字
  value?: string;
}

const props = withDefaults(defineProps<Props>(), {
  color: 'purple',
  top: '0',
  right: '0',
  width: '100px',
  height: '100px',
  title: 'Title',
  icon: undefined,
  value: '$0',
});

const colorTheme = props.color;
const position = { top: props.top, right: props.right };
const size = { width: props.width, height: props.height };
</script>

<style scoped>
.bubble {
  position: absolute;
  border-radius: 50%;
  padding: 12px;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  animation: float 6s ease-in-out infinite;
}

.bubble span {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 6px; /* 与下层内容增加间距 */
}

.bubble b {
  font-size: 18px;
  margin-top: 4px;
}

/* 图标样式：控制大小和间距 */
.bubble-icon {
  width: 48px;
  height: 48px;
  margin-top: 4px;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-12px); }
  100% { transform: translateY(0px); }
}

/* 颜色主题 */
.bubble.purple {
  background: linear-gradient(135deg, #6C5CE7, #A29BFE);
  animation-delay: 0s;
}
.bubble.blue {
  background: linear-gradient(135deg, #0984E3, #74B9FF);
  animation-delay: 1s;
}
.bubble.orange {
  background: linear-gradient(135deg, #E17055, #FF7675);
  animation-delay: 2s;
}
</style>