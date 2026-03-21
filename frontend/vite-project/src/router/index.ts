// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './router.ts'

const router = createRouter({
  history: createWebHistory(),
  routes,
  strict: true,
  scrollBehavior: () => ({ left: 0, top: 0 })
})

export default router