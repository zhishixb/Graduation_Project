<template>
  <div class="graduation-project-container">
    <SideMenu></SideMenu>

    <div class="graduation-project-child-page">
      <!-- 1. RouterView 改为使用 v-slot -->
      <router-view v-slot="{ Component, route }">
        <!-- 2. transition 包裹 component -->
        <transition name="fade" mode="out-in">
          <!-- 3. 动态渲染组件，并绑定 key -->
          <component :is="Component" :key="route.fullPath" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import SideMenu from "@/components/graduation_project/menu/SideMenu.vue";
</script>

<style scoped>
.graduation-project-container {
  width: 100%;
  height: 100%;
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f7efff, #e9f6ff);
  overflow: hidden;
}

.graduation-project-child-page {
  width: 980px;
  height: 560px;
  border-radius: 8px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from {
  opacity: 0;
}

.fade-leave-to {
  opacity: 0;
}
</style>