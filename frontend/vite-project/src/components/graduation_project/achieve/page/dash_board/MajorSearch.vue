<template>
  <div
    class="expandable-wrapper content-wrapper"
    :class="{ expanded: isExpanded, 'fade-in': showReveal }"
    @click="toggle"
  >
    <div class="block" :class="{ expanded: isExpanded }">
      <div class="block-content" @click.stop>
        <NCascader
          v-model:value="majorValue"
          :options="majorOptions"
          placeholder="专业查询"
          class="cascader-override"
          size="medium"
          :show-path="false"
          clearable
        />
        <button class="search-btn" @click="handleSearch">
          <SearchOutline />
        </button>
      </div>
    </div>

    <!-- 标签改为纵向排列，包含主文字和副文字 -->
    <div class="label" :class="{ hide: isExpanded }">
      <span class="label-text">专业查询</span>
      <span class="label-sub">点击查看</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue';
import { NCascader } from 'naive-ui';
import { SearchOutline } from '@vicons/ionicons5';
import { getMajorStatus } from "@/apis/business.ts"
import { useDataStore } from '@/stores/achieve/dataStore.ts';
import { useBusinessStore} from '@/stores/achieve/business.ts';

const store = useDataStore()
const businessStore = useBusinessStore()

const props = withDefaults(defineProps<{
  reveal?: boolean;
}>(), {
  reveal: false,
});

const isExpanded = ref(false);
const majorValue = ref(null);
const majorOptions = ref([])

const emit = defineEmits(['search']);

const toggle = () => {
  isExpanded.value = !isExpanded.value;
};

const handleSearch = () => {
  emit('search', majorValue.value);
  store.selectMajorName(majorValue.value)
  store.isLoading = true
    setTimeout(() => {
    store.turnToPage("majorDetail")
  }, 400);
};

// --- 淡入控制逻辑 ---
const showReveal = ref(false);
let timer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.reveal,
  (newVal) => {
    if (timer) clearTimeout(timer);
    if (newVal) {
      timer = setTimeout(() => {
        showReveal.value = true;
      }, 20);
    } else {
      showReveal.value = false;
    }
  },
  { immediate: true }
);

onMounted(async () => {
  try {
    const res = await getMajorStatus()
    if (res.success) {
      majorOptions.value = businessStore.buildMajorCascaderTree(res.data)
    } else {
      // 错误处理
    }
  } catch (err) {
    console.error(err)
  }
})

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer);
});
</script>

<style scoped>
.expandable-wrapper {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;

  /* 淡入动画基础设置 */
  position: relative;
  z-index: 1;
}

/* 内容包裹层淡入 */
.content-wrapper {
  opacity: 0;
  transition: opacity 0.6s ease;
}

.fade-in {
  opacity: 1;
  transition-delay: 0.8s;
}

/* 鲜艳渐变背景 */
.block {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #FF6B6B, #FF8E53);
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
  transition: width 0.5s cubic-bezier(0.34, 0.69, 0.1, 1.05) 0.25s,
              height 0.5s cubic-bezier(0.34, 0.69, 0.1, 1.05) 0.25s,
              background 0.3s,
              box-shadow 0.3s ease;
}

.block.expanded {
  width: 180px;
  height: 36px;
  box-shadow: 0 8px 24px rgba(255, 107, 107, 0.4);
}

.block-content {
  display: flex;
  align-items: center;
  width: 100%;
  height: 100%;
  padding: 0 12px;
  gap: 12px;
  box-sizing: border-box;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0s 0.2s;
}

.block.expanded .block-content {
  opacity: 1;
  visibility: visible;
  transition: opacity 0.2s ease 0.75s, visibility 0s 0.75s;
}

.cascader-override {
  flex: 1;
  min-width: 0;
}

/* 按钮和图标改为白色 */
.search-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #fff;
  transition: opacity 0.2s;
}
.search-btn:hover {
  opacity: 0.5;
}
.search-btn svg {
  width: 20px;
  height: 20px;
  fill: #fff;
}

/* 标签容器改为纵向排列，添加副文字 */
.label {
  margin-left: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.4;
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.label.hide {
  opacity: 0;
  transform: translateX(-8px);
  pointer-events: none;
}

/* 主文字保持鲜艳风格 */
.label-text {
  font-size: 12px;
  font-weight: 600;
  color: #FF6B6B;
}

/* 副文字淡化处理 */
.label-sub {
  font-size: 10px;
  color: rgba(255, 107, 107, 0.65);
}

/* 级联选择器内文字和图标改为白色 */
:deep(.cascader-override),
:deep(.cascader-override *) {
  background: transparent !important;
  background-color: transparent !important;
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
  color: rgba(255, 255, 255, 0.9) !important;
  fill: rgba(255, 255, 255, 0.9) !important;
}
:deep(.cascader-override .n-base-selection-input__content),
:deep(.cascader-override .n-base-selection-tag) {
  color: #fff !important;
}
</style>