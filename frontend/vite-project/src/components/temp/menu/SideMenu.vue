<template>
  <div class="side-menu">
    <div class="menu-header">Menu</div>
    <div class="menu-wrapper">
      <n-menu
        :options="menuOptions"
        key-field="whateverKey"
        mode="vertical"
        :indent="18"
        :collapsed="false"
        @update:value="handleMenuSelect"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { h } from 'vue'
import { useRouter } from 'vue-router'
import type { MenuOption } from 'naive-ui'
// ✅ 修复 1: 导入 NIcon
import { NIcon } from 'naive-ui'
import {
  GridOutline,
  BugOutline,
  HardwareChipOutline,
  EaselOutline,
  ArrowBackCircleOutline
} from '@vicons/ionicons5'

const router = useRouter()

const routeMap: Record<string, string> = {
  home: '/graduation_project',
  spider: '/graduation_project/spider',
  process: '/graduation_project/process',
  // 补充缺失的路由映射，防止点击报错
  achieve: '/graduation_project/achieve',
  back: '/'
}

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions: MenuOption[] = [
  {
    label: '毕业设计',
    whateverKey: 'home',
    icon: renderIcon(GridOutline)
  },
  {
    label: '爬虫详情',
    whateverKey: 'spider',
    icon: renderIcon(BugOutline)
  },
  {
    label: '数据处理',
    whateverKey: 'process',
    icon: renderIcon(HardwareChipOutline)
  },
  {
    label: '成果展示',
    whateverKey: 'achieve',
    icon: renderIcon(EaselOutline)
  },
  {
    label: '退出',
    whateverKey: 'back',
    icon: renderIcon(ArrowBackCircleOutline)
  }
]

const handleMenuSelect = (key: string) => {
  const path = routeMap[key]
  if (path) {
    router.push(path)
  }
}
</script>

<style scoped>
.side-menu {
  /* ✅ 修复 2: 增加宽度以容纳文字 (中文通常需要 160px-200px) */
  width: 160px;
  height: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center; /* 保持整体居中 */
  background-color: white;
  box-shadow: 2px 0 8px rgba(0,0,0,0.05);
  overflow: hidden;
}

.menu-header {
  height: 60px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 10px;
  font-weight: bold;
  color: #333;
}

.menu-wrapper {
  /* ✅ 修复 3: 宽度设为 100%，不再限制为 60px，让文字有空间展开 */
  width: 100%;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  /* 去掉 justify-content: center，让菜单自然左对齐 */
}

/* 确保 n-menu 宽度填满父容器 */
:deep(.n-menu) {
  width: 100%;
}

/* 菜单项视觉优化 */
:deep(.n-menu-item-content--selected)::before {
  background-color: #dbeafe !important;
  border-radius: 8px;
}

:deep(.n-menu-item-content):hover::before,
:deep(.n-menu-item-content)::before {
  border-radius: 8px;
}

:deep(.n-menu-item-content--selected .n-menu-item-content__icon) {
  color: #2563eb !important;
}

/* 确保文字部分可见 (以防万一有其他全局样式干扰) */
:deep(.n-menu-item-content-header) {
  display: block !important;
  white-space: nowrap; /* 防止文字换行 */
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.n-menu) {
  --n-item-text-color-active: #2563eb !important;
  --n-item-icon-color-active: #2563eb !important;
  --n-item-color-active: rgba(37, 99, 235, 0.1) !important;
  --n-item-text-color-active-hover: #152d7c !important;
  --n-item-icon-color-active-hover: #152d7c !important;
}
</style>