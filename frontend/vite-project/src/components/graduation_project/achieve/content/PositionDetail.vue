<template>
  <div class="majordetail-content">
    <!-- 左侧岗位详情面板 -->
    <div
      v-if="jobData"
      class="left-panel"
      :class="{ 'fade-in': showPanels }"
    >
      <JobInfoPanel
        :job-data="jobData"
      />
    </div>

    <!-- 右侧匹配专业 + 词云面板 -->
    <div
      v-if="matchList"
      class="right-panel"
      :class="{ 'fade-in': showPanels }"
    >
      <div style="margin-top: 135px"></div>
      <MatchList :data="matchList" />
      <WordCloud style="margin-left: -50px" :data="wordCloud" :width="360" :height="280" />
    </div>

    <!-- 地图动画区域 -->
    <div
      class="map-stage"
      :class="stageClass"
      @transitionend="onTransitionEnd"
    >
      <Map :data="provinceData" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Map from '@/components/graduation_project/achieve/animated/Diagram.vue'
import MatchList from '@/components/graduation_project/achieve/page/job_detail/MatchList.vue'
import WordCloud from '@/components/graduation_project/achieve/page/job_detail/WordCloud.vue'
import JobInfoPanel from '@/components/graduation_project/achieve/page/job_detail/JobInfoPanel.vue'
import { useDataStore } from '@/stores/achieve/dataStore.ts'
import {
  getJobProvinceCount,
  getJobSkills,
  getMajorsByFunction,
  getJobSkillsCount
} from "@/apis/business.ts"

const store = useDataStore()
const stage = ref<'initial' | 'scaled' | 'moved'>('initial')
const showPanels = ref(false)
let scaledEnded = false

const jobData = ref()
const matchList = ref()
const wordCloud = ref<{ name: string; value: number }[]>([])
const provinceData = ref()

const stageClass = computed(() => {
  if (stage.value === 'moved') return 'scaled moved'
  if (stage.value === 'scaled') return 'scaled'
  return ''
})

const onTransitionEnd = (e: TransitionEvent) => {
  if (stage.value === 'scaled' && !scaledEnded && e.propertyName === 'transform') {
    scaledEnded = true
    stage.value = 'moved'
  }
  else if (stage.value === 'moved' && (e.propertyName === 'left' || e.propertyName === 'top')) {
    if (!showPanels.value) {
      showPanels.value = true
    }
  }
}

onMounted(async () => {
  const job = store.getterJobName()
  const res_1 = await getJobSkills(job)
  jobData.value = res_1.data

  console.log(jobData.value)

  // 确保 jobData 有 function_name
  if (!jobData.value?.function_name) {
    console.error('jobData 缺少 function_name')
    return
  }

  const res_2 = await getMajorsByFunction(jobData.value.function_name)
  matchList.value = Array.isArray(res_2.data) ? res_2.data : []

  // 构造岗位名称数组
  const functionNameList = [jobData.value.function_name]
  const res_3 = await getJobProvinceCount(functionNameList)
  provinceData.value = res_3.data

  // 获取技能词频数据（需 uid）
  if (jobData.value?.uid) {
    const res_4 = await getJobSkillsCount(jobData.value.uid)
    if (res_4.success && Array.isArray(res_4.data?.skills)) {
      wordCloud.value = res_4.data.skills.map((item: { skill: string; count: number }) => ({
        name: item.skill,
        value: item.count
      }))
    }
  } else {
    console.warn('jobData 缺少 uid，无法获取技能词频')
  }

  setTimeout(() => store.isLoading = false, 400)
  setTimeout(() => {
    requestAnimationFrame(() => {
      stage.value = 'scaled'
    })
  }, 400 + 800)
})
</script>

<style scoped>
.majordetail-content {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

/* ---- 面板淡入 ---- */
.left-panel,
.right-panel {
  opacity: 0;
  transition: opacity 0.6s ease;
}
.left-panel.fade-in,
.right-panel.fade-in {
  opacity: 1;
  transition-delay: 0.8s;
}

/* 左侧面板 */
.left-panel {
  position: absolute;
  left: 0;
  top: 0;
  width: 300px;
  height: 100%;
  overflow-y: auto;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 1;
  pointer-events: auto;
  box-sizing: border-box;
}

/* 左侧滚动条美化 */
.left-panel::-webkit-scrollbar {
  width: 4px;
}
.left-panel::-webkit-scrollbar-track {
  background: transparent;
}
.left-panel::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 2px;
}

/* 右侧面板 */
.right-panel {
  position: absolute;
  left: 330px;
  top: 0;
  width: 400px;
  height: 100%;
  overflow-y: auto;
  z-index: 1;
  pointer-events: auto;
  box-sizing: border-box;
}

.right-panel::-webkit-scrollbar {
  width: 4px;
}
.right-panel::-webkit-scrollbar-track {
  background: transparent;
}
.right-panel::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 2px;
}

/* ---- 地图动画（保持居中逻辑不变） ---- */
.map-stage {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  transition: transform 0.8s cubic-bezier(0.25, 0.8, 0.25, 1),
              left 0.8s cubic-bezier(0.25, 0.8, 0.25, 1),
              top 0.8s cubic-bezier(0.25, 0.8, 0.25, 1);
  z-index: 5;
  pointer-events: auto;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.map-stage.scaled {
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%) scale(0.6);
}

.map-stage.scaled.moved {
  left: 930px;
  top: 445px;
  transform: translate(-50%, -50%) scale(0.6);
}
</style>