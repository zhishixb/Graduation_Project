// vite.config.ts
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 自动导入
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import { VitePWA } from 'vite-plugin-pwa' // 1. 引入插件

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
        registerType: 'autoUpdate', // 自动更新策略
        includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'], // 需要缓存的静态资源
        manifest: {
          name: '我的桌面助手', // 应用全名
          short_name: '桌面助手', // 桌面图标下的名字
          description: '基于 FastAPI + Vue 的本地智能工具',
          theme_color: '#ffffff', // 浏览器主题色
          background_color: '#ffffff', // 启动页背景色
          display: 'standalone', // 👈 关键：隐藏地址栏，像原生应用
          orientation: 'portrait',
          scope: '/',
          start_url: '/',
          icons: [
            {
              src: 'pwa-192x192.png', // 确保你在 public 文件夹放了这个图标
              sizes: '192x192',
              type: 'image/png'
            },
            {
              src: 'pwa-512x512.png', // 确保你在 public 文件夹放了这个图标
              sizes: '512x512',
              type: 'image/png'
            },
            {
              src: 'pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any maskable' // 支持安卓自适应图标
            }
          ]
        },
        workbox: {
          // 缓存策略：缓存所有静态资源
          globPatterns: ['**/*.{js,css,html,ico,png,svg,jpg,jpeg}'],
          // 运行时缓存示例：缓存 API 请求 (可选，根据你的 FastAPI 路由调整)
          // runtimeCaching: [{
          //   urlPattern: /^https:\/\/your-api-domain\.com\/api\/.*/i,
          //   handler: 'NetworkFirst',
          //   options: {
          //     cacheName: 'api-cache',
          //     expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 * 24 },
          //     cacheableResponse: { statuses: [0, 200] }
          //   }
          // }]
        }
      }),

    // 自动导入 Vue API 和 Naive UI 组合式函数（如 useMessage）
    AutoImport({
      imports: ['vue'],
      resolvers: [NaiveUiResolver()],
      dts: 'src/auto-imports.d.ts', // 生成类型声明
      eslintrc: {
        enabled: false // 若使用 ESLint 可开启自动生成规则
      }
    }),

    // 自动注册 Naive UI 组件（如 <n-button>）
    Components({
      resolvers: [NaiveUiResolver()],
      dts: 'src/public.d.ts' // 生成全局组件类型
    })
  ],

  css: {
    preprocessorOptions: {
      // Naive UI 推荐使用 CSS 变量，无需预处理器
      // 如果你不用 less/scss，可以删除整个 css 配置
    }
  },

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  server: {
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8090',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})