<!-- components/graduation_project/achieve/page/dash_board/BubbleMarker.vue -->
<template>
  <Bubble
    :color="color"
    :color-end="colorEnd"
    :shadow-opacity="shadowOpacity"
    :shadow-opacity-hover="shadowOpacityHover"
  >
    <template #icon>
      <n-icon size="18" color="white">
        <component :is="iconComponent" />
      </n-icon>
    </template>
    {{ labelText }}
  </Bubble>
</template>

<script setup>
import Bubble from '@/components/graduation_project/achieve/page/dash_board/Bubble.vue'

defineProps({
  iconComponent: { type: Object, required: true },
  labelText: { type: String, default: '' },
  color: { type: String, default: '#a0c4ff' },
  colorEnd: { type: String, default: '#bdb2ff' },
  shadowOpacity: { type: Number, default: 0.4 },
  shadowOpacityHover: { type: Number, default: 0.5 }
})
</script>