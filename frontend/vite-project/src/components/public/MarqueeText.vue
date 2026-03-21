<template>
  <div class="marquee-wrapper" ref="wrapperRef">
    <div
      class="marquee-content"
      ref="contentRef"
      :class="{ 'is-moving': isMoving }"
      :style="{
        color: color,
        fontWeight: bold ? 'bold' : 'normal',
        '--move-distance': moveDistance,
        '--duration': `${speed}s`
      }"
    >
      {{ text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'

// --- Props 定义 ---
interface Props {
  text: string           // 滚动的文本内容
  speed?: number         // 单程动画时间 (秒)，默认 5 秒
  color?: string         // 文字颜色
  bold?: boolean         // 是否加粗
}

const props = withDefaults(defineProps<Props>(), {
  speed: 5,
  color: 'inherit',
  bold: false
})

// --- 状态 ---
const wrapperRef = ref<HTMLElement | null>(null)
const contentRef = ref<HTMLElement | null>(null)
const moveDistance = ref<string>('0px')
const isMoving = ref<boolean>(false)

// --- 核心逻辑：计算距离 ---
const calculateMoveDistance = () => {
  if (!wrapperRef.value || !contentRef.value) return

  const containerWidth = wrapperRef.value.offsetWidth
  const textWidth = contentRef.value.offsetWidth

  if (textWidth <= containerWidth) {
    // 文字太短，不滚动
    moveDistance.value = '0px'
    isMoving.value = false
  } else {
    // 计算需要移动的距离 (负值)
    moveDistance.value = `${containerWidth - textWidth}px`
    isMoving.value = true
  }
}

// --- 生命周期 ---
onMounted(() => {
  nextTick(calculateMoveDistance)
  // 监听窗口大小变化，确保响应式
  window.addEventListener('resize', calculateMoveDistance)
})

watch(() => props.text, () => {
  nextTick(calculateMoveDistance)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', calculateMoveDistance)
})
</script>

<style scoped>
/* 声明 CSS 变量默认值 */
.marquee-content {
  --move-distance: 0px;
  --duration: 5s;
}

.marquee-wrapper {
  width: 100%;
  overflow: hidden;       /* 必须：隐藏溢出 */
  white-space: nowrap;    /* 必须：不换行 */
  position: relative;
  display: block;
}

.marquee-content {
  display: inline-block;  /* 必须：让宽度等于内容宽度 */
  transform: translateX(0);
  will-change: transform;
}

/* 只有文字过长时才添加此类名，启动动画 */
.marquee-content.is-moving {
  animation: scroll-back-forth var(--duration) ease-in-out infinite alternate;
}

@keyframes scroll-back-forth {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(var(--move-distance));
  }
}
</style>