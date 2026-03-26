import type { RouteRecordRaw } from 'vue-router'

import GraduationProject from '@/views/graduation_project/index.vue'
import Spider from  '@/views/graduation_project/pages/Spider.vue'
import Process from "@/views/graduation_project/pages/Process.vue";

import Test from "@/views/Test/Test.vue";


export const routes: RouteRecordRaw[] = [
    {
        path: '/graduation_project',
        name: 'GraduationProject',
        component: GraduationProject,
        meta: {
          title: '毕业设计演示',
          requireAuth: false
        },
        children:[
            {
                path: 'spider',
                name: 'Spider',
                component: Spider,
                meta: {
                    title: '爬虫面板',
                    requireAuth: false
                }
            },
            {
                path: 'process',
                name: 'Process',
                component: Process,
                meta: {
                    title: '数据处理',
                    requireAuth: false
                }
            },
        ]
    },
    {
        path: '/test',
        name: 'Test',
        component: Test,
        meta: {
          title: '毕业设计演示',
          requireAuth: false
        },
        children:[
            // {
            //     path: 'spider',
            //     name: 'Spider',
            //     component: Spider,
            //     meta: {
            //         title: '爬虫面板',
            //         requireAuth: false
            //     }
            // },
        ]
    }
]