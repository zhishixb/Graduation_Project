<template>
  <div class="side-menu">
    <div class="menu-header">Header</div>
    <div class="menu-wrapper">
      <n-menu
        :options="menuOptions"
        key-field="whateverKey"
        mode="vertical"
        :indent="18"
        @update:value="handleMenuSelect"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { h } from 'vue'
import { useRouter } from 'vue-router'
import type { MenuOption } from 'naive-ui'
import {
  GridOutline,
  BugOutline,
  HardwareChipOutline,
  EaselOutline,
  ArrowBackCircleOutline
} from '@vicons/ionicons5'

const router = useRouter()

// 路由映射
const routeMap: Record<string, string> = {
  home: '/graduation_project',
  spider: '/graduation_project/spider',
  process: '/graduation_project/process',
  achieve: '/graduation_project/achieve'
}

// 菜单配置（注意：不传 label 或设为 ''，避免占位）
function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}


const menuOptions: MenuOption[] = [
  {
    whateverLabel: '毕业设计',
    whateverKey: 'home',
    icon: renderIcon(GridOutline)
  },
  {
    whateverLabel: '爬虫详情',
    whateverKey: 'spider',
    icon: renderIcon(BugOutline)
  },
  {
    whateverLabel: '数据处理',
    whateverKey: 'process',
    icon: renderIcon(HardwareChipOutline)
  },
  {
    whateverLabel: '成果展示',
    whateverKey: 'achieve',
    icon: renderIcon(EaselOutline)
  },
  {
    whateverLabel: '退出',
    whateverKey: 'back',
    icon: renderIcon(ArrowBackCircleOutline)
  }
]

// 菜单点击处理
const handleMenuSelect = (key: string) => {
  const path = routeMap[key]
  if (path) {
    router.push(path)
  }
}
</script>

<style scoped>
.side-menu {
  width: 70px;
  height: 560px;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.2);
  animation: breathe 2s infinite ease-in-out;
  overflow: hidden;
}

.menu-header {
  height: 60px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  border-bottom: 1px solid #c1c1c1;
  margin-bottom: 30px;
}

.menu-wrapper {
  width: 60px;
  flex: 1;
  min-height: 0;
  /* 确保菜单内容水平居中 */
  display: flex;
  justify-content: center;
}

/* 防止 n-menu 自身宽度撑开 */
:deep(.n-menu) {
  width: auto;
}

/* 菜单项视觉优化 */
:deep(.n-menu-item-content--selected)::before {
  background-color: #dbeafe !important;
  border-radius: 8px;
}
:deep(.n-menu-item-content):hover::before,
:deep(.n-menu-item-content)::before {
  border-radius: 8px;
  font-weight: bolder;
}
:deep(.n-menu-item-content--selected .n-menu-item-content__icon) {
  color: #2563eb !important;
}

/* 关键：隐藏空 label 产生的占位（即使不传 label，Naive 也可能留空间） */
:deep(.n-menu-item-content-header) {
  display: none !important;
}
</style>