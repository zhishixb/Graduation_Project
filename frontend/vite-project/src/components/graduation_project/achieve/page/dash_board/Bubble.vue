<!-- components/Bubble.vue -->
<template>
  <div class="bubble-wrapper">
    <div
      class="bubble"
      :class="{ show: isVisible }"
      :style="bubbleStyle"
    >
      <span class="text-wrapper">
        <span class="short-content">
          <slot name="icon">
            <span class="default-icon">●</span>
          </slot>
        </span>
        <span class="full-content">
          <slot>默认文字</slot>
        </span>
      </span>
      <div class="bubble-arrow"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  color: { type: String, default: '#a0c4ff' },   // 渐变起始色
  colorEnd: { type: String, default: '#bdb2ff' }, // 渐变结束色 / 箭头色
  shadowOpacity: { type: Number, default: 0.4 },
  shadowOpacityHover: { type: Number, default: 0.5 }
})

const isVisible = ref(false)

const handleLoad = () => {
  setTimeout(() => {
    isVisible.value = true
  }, 200)
}

onMounted(() => {
  if (document.readyState === 'complete') {
    handleLoad()
  } else {
    window.addEventListener('load', handleLoad)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('load', handleLoad)
})

// 将 hex 颜色转为 rgb 对象（用于生成带透明度的阴影）
const hexToRgb = (hex: string) => {
  hex = hex.replace('#', '')
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('')
  const num = parseInt(hex, 16)
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  }
}

const bubbleStyle = computed(() => {
  const start = props.color
  const end = props.colorEnd
  const startRgb = hexToRgb(start)
  const shadow = startRgb
    ? `rgba(${startRgb.r}, ${startRgb.g}, ${startRgb.b}, ${props.shadowOpacity})`
    : `rgba(160,196,255,${props.shadowOpacity})`
  const shadowHover = startRgb
    ? `rgba(${startRgb.r}, ${startRgb.g}, ${startRgb.b}, ${props.shadowOpacityHover})`
    : `rgba(160,196,255,${props.shadowOpacityHover})`

  return {
    '--bubble-bg': `linear-gradient(135deg, ${start}, ${end})`,
    '--bubble-shadow': `0 8px 24px ${shadow}`,
    '--bubble-shadow-hover': `0 10px 30px ${shadowHover}`,
    '--bubble-arrow-color': end
  }
})
</script>

<style scoped>
.bubble-wrapper {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 120px;
  position: relative;
}

.bubble {
  width: 40px;
  height: 40px;
  position: relative;
  background: var(--bubble-bg, linear-gradient(135deg, #a0c4ff, #bdb2ff));
  border-radius: 8px;
  box-shadow: var(--bubble-shadow, 0 8px 24px rgba(160, 196, 255, 0.4));
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  user-select: none;
  opacity: 0;
  transform: translateY(30px);
  transition:
    opacity 0.8s ease 0.2s,
    transform 0.8s ease 0.2s,
    width 0.3s ease,
    box-shadow 0.3s ease;
}

.bubble.show {
  opacity: 1;
  transform: translateY(0);
}

.bubble.show:hover {
  width: 160px;
  box-shadow: var(--bubble-shadow-hover, 0 10px 30px rgba(160, 196, 255, 0.5));
  transform: translateY(-2px);
}

.bubble-arrow {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 10px solid var(--bubble-arrow-color, #bdb2ff);
}

.text-wrapper {
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
}

.short-content {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.full-content {
  color: white;
  display: inline-block;
  max-width: 0;
  overflow: hidden;
  opacity: 0;
  white-space: nowrap;
  transition:
    max-width 0.3s ease,
    opacity 0.3s ease;
  margin-left: 4px;
}

.bubble.show:hover .full-content {
  max-width: 120px;
  opacity: 1;
}

.default-icon {
  font-size: 18px;
  color: white;
}
</style>