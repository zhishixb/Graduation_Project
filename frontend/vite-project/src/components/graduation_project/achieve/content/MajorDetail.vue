<template>
  <div class="majordetail-content">
    <!-- 左侧专业信息面板 -->
    <div
      v-if="majorData"
      class="left-panel"
      :class="{ 'fade-in': showPanels }"
    >
      <MajorInfoPanel
        :major-name="store.getterMajorName()"
        :major-data="majorData"
      />
    </div>

    <!-- 右侧匹配岗位面板 -->
    <div
      v-if="matchList"
      class="right-panel"
      :class="{ 'fade-in': showPanels }"
    >
      <div style="margin-top: 180px"></div>
      <MatchList :data="matchList" />
      <CommunityRecognition style="margin-top: 20px" v-if="communityComment" :data="communityComment" />
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
import MatchList from '@/components/graduation_project/achieve/page/major_detail/MatchList.vue'
import MajorInfoPanel from '@/components/graduation_project/achieve/page/major_detail/MajorInfoPanel.vue'
import CommunityRecognition from '@/components/graduation_project/achieve/page/major_detail/CommunityRecognition.vue'
import { useDataStore } from '@/stores/achieve/dataStore.ts'
import { getFunctionsByMajor, getMajorData, getJobProvinceCount, getSentimentAnalysis } from "@/apis/business.ts"

const store = useDataStore()
const stage = ref<'initial' | 'scaled' | 'moved'>('initial')
const showPanels = ref(false)
let scaledEnded = false

const majorData = ref()
const matchList = ref()
const provinceData = ref()
const communityComment = ref()

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
  const major = store.getterMajorName()
  const res_1 = await getFunctionsByMajor(major)
  matchList.value = res_1.data
  const res_2 = await getMajorData(major)
  majorData.value = res_2.data
  const functionNameList = matchList.value.map(item => item.function_name);
  const res_3 = await getJobProvinceCount(functionNameList)
  provinceData.value = res_3.data
  const res_4 = await getSentimentAnalysis(major)
  communityComment.value = res_4.data
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

/* 左侧面板：330px，自带滚动 */
.left-panel {
  position: absolute;
  left: 0;
  top: 0;
  width: 300px;          /* 由 300px 改为 330px */
  height: 100%;
  overflow-y: auto;       /* 开启纵向滚动 */
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

/* 右侧面板：left 同步至 330px */
.right-panel {
  position: absolute;
  left: 330px;           /* 紧贴左侧 330px */
  top: 0;
  width: 420px;
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