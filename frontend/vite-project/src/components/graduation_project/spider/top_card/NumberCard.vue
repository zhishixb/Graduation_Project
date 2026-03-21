<template>
  <div class="number-card">
    <div class="number-card-left">
      <div class="number-card-title">岗位信息数</div>
      <div class="number-card-count">
        <n-number-animation ref="numberAnimationInstRef" :from="0" :to="formattedCount" />
      </div>
      <div class="number-card-time" v-if="lastJobData">
        最后更新：<br>{{ formattedTime }}
      </div>
      <n-button type="info" round style="height: 25px; width: 65px;" strong secondary @click="handleUpdateClick">更新</n-button>
    </div>
    <div class="number-card-right"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'

const message = useMessage()

// 定义 props
const props = defineProps<{
  lastJobData: { time: string; count: number } | null
}>()

const emit = defineEmits<{
  (e: 'update-request'): void
}>()

// 格式化数量（如 3,199）
const formattedCount = computed(() => {
  if (!props.lastJobData) return '--'
  return props.lastJobData.count
})

// 格式化时间（如 "01-02 20:27"）
const formattedTime = computed(() => {
  if (!props.lastJobData) return ''
  const t = props.lastJobData.time // "2026-01-02 20:27:58"
  const datePart = t.split(' ')[0].slice(5) // "01-02"
  const timePart = t.split(' ')[1].slice(0, 5) // "20:27"
  return `${datePart} ${timePart}`
})

const handleUpdateClick = () => {
  const pyapi = (window as any).pyapi
  if (!pyapi) {
    message.error('PyAPI 未注入')
    return
  }
  try {
   pyapi.count_spider_boss()
  } catch (error) {
    message.error('统计岗位数据失败，请稍后重试')
  }
  emit('update-request') // 触发事件，通知父组件
}

// 示例：在组件挂载时检查并可能触发错误消息（根据需求调整）
onMounted(() => {
})
</script>

<style scoped>
/* 样式保持不变 */
.number-card {
  width: 240px;
  height: 150px;
  border-radius: 8px;
  display: flex;
  gap: 10px;
  background-color: #fefefe;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.number-card-left {
  width: 80px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
}

.number-card-right {
  width: 90px;
  height: 120px;
  padding: 15px;
}


.number-card-title {
  font-size: 11px;
  color: #999999;
  margin-bottom: 6px;
}

.number-card-count {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.number-card-time {
  font-size: 10px;
  color: #888;
  margin-bottom: 5px;
}
</style>