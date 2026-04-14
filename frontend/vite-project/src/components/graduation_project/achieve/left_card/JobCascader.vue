<!-- components/JobCascader.vue -->
<template>
  <div class="balance-item expense">
    <NCascader
      v-model:value="jobValue"
      :options="jobOptions"
      placeholder="岗位查询"
      class="cascader-override"
      size="medium"
      :show-path="false"
      clearable
    />
    <button class="search-btn" @click="handleSearch">
      <SearchOutline />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { NCascader } from 'naive-ui';
import { SearchOutline } from '@vicons/ionicons5';

const jobValue = ref(null);
const jobOptions = [
  {
    label: '技术类',
    value: 'tech',
    children: [
      { label: '前端工程师', value: 'frontend' },
      { label: '后端工程师', value: 'backend' },
      { label: '全栈工程师', value: 'fullstack' },
    ],
  },
  {
    label: '金融类',
    value: 'finance',
    children: [
      { label: '分析师', value: 'analyst' },
      { label: '风控专员', value: 'risk' },
      { label: '投行顾问', value: 'ib' },
    ],
  },
  {
    label: '设计类',
    value: 'design',
    children: [
      { label: 'UI设计师', value: 'ui' },
      { label: 'UX设计师', value: 'ux' },
    ],
  },
];

const emit = defineEmits(['search']);

const handleSearch = () => {
  emit('search', jobValue.value);
};
</script>

<style scoped>
.balance-item {
  padding: 12px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: white;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}
.expense {
  background: #6C5CE7;
}
.cascader-override {
  flex: 1;
}
.search-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: white;
  transition: opacity 0.2s;
}
.search-btn:hover {
  opacity: 0.8;
}
.search-btn svg {
  width: 20px;
  height: 20px;
  fill: white;
}

/* 级联选择器透明样式 */
:deep(.cascader-override),
:deep(.cascader-override *) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}
:deep(.cascader-override .n-base-selection),
:deep(.cascader-override .n-base-selection__border),
:deep(.cascader-override .n-base-selection__state-border),
:deep(.cascader-override .n-input__wrapper),
:deep(.cascader-override .n-input__wrapper--hover),
:deep(.cascader-override .n-input__wrapper--focus) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}
:deep(.cascader-override) {
  --n-border: transparent !important;
  --n-border-active: transparent !important;
  --n-border-focus: transparent !important;
  --n-border-hover: transparent !important;
  --n-color: transparent !important;
  --n-color-active: transparent !important;
  --n-color-disabled: transparent !important;
  --n-box-shadow-active: none !important;
  --n-box-shadow-focus: none !important;
  --n-box-shadow-hover: none !important;
}
:deep(.cascader-override .n-base-selection-placeholder__inner),
:deep(.cascader-override .n-base-selection-label__render-label),
:deep(.cascader-override .n-base-suffix__arrow svg) {
  color: white !important;
  fill: white !important;
}
:deep(.cascader-override .n-base-selection-input__content),
:deep(.cascader-override .n-base-selection-tag) {
  color: white !important;
}
</style>