<template>
  <div class="achieve-container">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar">
      <div class="logo-area">
        <div class="logo-content">
          <div class="logo-icon">M</div>
          <span class="logo-text">Match</span>
        </div>
      </div>

      <div class="services-section">
      </div>

      <div class="bottom-icons">
        <div class="icon-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1Z"/></svg></div>
        <div class="icon-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div>
        <div class="icon-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg></div>
      </div>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="main-content" :class="{ 'reveal-active': store.isLoading }">
      <!-- <canvas ref="waveCanvas" class="wave-canvas"></canvas> -->
      <!-- 白色遮罩动画层 -->
      <div class="bg-fill"></div>

      <div class="map-background">
        <Map style="margin-left: -40px;" v-show="store.toDashBoard"></Map>
      </div>

      <div class="content-container">
        <DashBoard v-show="store.toDashBoard"></DashBoard>
        <MajorDetail v-if="store.toMajorDetail"></MajorDetail>
        <PositionDetail v-if="store.toPositionDetail"></PositionDetail>
        <ComparePage v-if="store.toComparePage"></ComparePage>
        <HotMajorList v-if="store.toHotMajor"></HotMajorList>
      </div>
     
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useDataStore } from '@/stores/achieve/dataStore.ts';
import Map from "@/components/graduation_project/achieve/map/Map.vue";
import DashBoard from "@/components/graduation_project/achieve/content/DashBoard.vue";
import HotMajorList from "@/components/graduation_project/achieve/content/HotMajorList.vue";
import MajorDetail from '@/components/graduation_project/achieve/content/MajorDetail.vue';
import PositionDetail from '@/components/graduation_project/achieve/content/PositionDetail.vue';
import ComparePage from '@/components/graduation_project/achieve/content/ComparePage.vue';

const store = useDataStore()

// 子页面组件状态
const showHotForMajors = ref(false);
const showMatchScore = ref(false);

const toggleReveal = () => {
  store.isLoading = true
  setTimeout(() => {
    store.turnToPage("hotMajor")
  }, 400);
  setTimeout(() => {
    store.isLoading = false;
  }, 900);
};

// ==================== 波浪画布逻辑（保留，与水波纹无关） ====================
const waveCanvas = ref<HTMLCanvasElement | null>(null);
let animationId: number | null = null;
let ctx: CanvasRenderingContext2D | null = null;
let width = 400, height = 400;

let phase1 = 0, phase2 = 0, phase3 = 0;
const speed1 = 0.008, speed2 = 0.012, speed3 = 0.006;
const amp1 = 0.010, amp2 = 0.012, amp3 = 0.008;

function getRadius(angle: number, a1: number, a2: number, a3: number, p1: number, p2: number, p3: number, baseR: number) {
  let r = baseR;
  r += Math.cos(angle + p1) * a1 * baseR;
  r += Math.cos(2 * angle + p2) * a2 * baseR;
  r += Math.cos(3 * angle + p3) * a3 * baseR;
  return Math.min(baseR + baseR * 0.06, Math.max(baseR - baseR * 0.05, r));
}

function drawWave() {
  if (!ctx) return;
  const centerX = width / 2, centerY = height / 2;
  const baseR = Math.min(width, height) * 0.45;

  phase1 += speed1;
  phase2 += speed2;
  phase3 += speed3;

  const steps = 180;
  const verts: { x: number; y: number }[] = [];
  for (let i = 0; i <= steps; i++) {
    const angle = (i / steps) * Math.PI * 2;
    const r = getRadius(angle, amp1, amp2, amp3, phase1, phase2, phase3, baseR);
    verts.push({ x: centerX + Math.cos(angle) * r, y: centerY + Math.sin(angle) * r });
  }

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = 'rgba(255,182,215,0.6)';
  ctx.beginPath();
  ctx.moveTo(verts[0].x, verts[0].y);
  for (let i = 1; i < verts.length; i++) ctx.lineTo(verts[i].x, verts[i].y);
  ctx.closePath();
  ctx.fill();
}

function animate() {
  drawWave();
  animationId = requestAnimationFrame(animate);
}

function resizeCanvas() {
  if (!waveCanvas.value) return;
  width = height = 400;
  waveCanvas.value.width = width;
  waveCanvas.value.height = height;
  ctx = waveCanvas.value.getContext('2d');
}

function handleCardBool(value: boolean) {
  console.log('接收到的布尔值:', value);
  if (value) {
    setTimeout(() => {
      showMatchScore.value = true;
    }, 550);
  } else {
    showMatchScore.value = false;
  }
  showHotForMajors.value = value;
}

onMounted(() => {
  resizeCanvas();
  animate();
  window.addEventListener('resize', resizeCanvas);
});

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId);
  window.removeEventListener('resize', resizeCanvas);
});
</script>

<style scoped>
/* 全局重置与容器 */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.achieve-container {
  width: 1220px;
  height: 100%;
  background-color: #F4F6FC;
  border-radius: 30px;
  display: flex;
  flex-direction: row;
  padding: 24px;
  gap: 24px;
  overflow: visible;
  position: relative;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.05);
}

/* 侧边栏样式 ———— 调整为 80px 宽度 */
.sidebar {
  width: 50px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 4px;
  z-index: 10;
}

.logo-area {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
  margin-left: -15px;
}

.logo-content {
  display: flex;
  align-items: center;
  font-weight: 700;
  font-size: 18px;
  color: #333;
}

.logo-content .logo-text {
  display: none; /* 隐藏文字，只留图标 */
}

.logo-icon {
  background: #FF6B6B;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.menu-icon {
  cursor: pointer;
  color: #888;
}

.profile-pic img {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  object-fit: cover;
}

.balance-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.services-section h4 {
  text-align: center;
  font-size: 12px;
  margin-bottom: 10px;
  color: #333;
}

.services-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.service-item {
  background: white;
  height: 64px;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #555;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.02);
}

.service-item svg {
  width: 20px;
  height: 20px;
}

.service-item:hover {
  transform: translateY(-2px);
}

.bottom-icons {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.icon-item {
  width: 36px;
  height: 36px;
  background: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  cursor: pointer;
}

/* 右侧主内容区 */
.main-content {
  flex: 1;
  height: 100%;
  position: relative;
  z-index: 1;
  overflow: visible;
  border-radius: 24px;
}

.map-background{
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  z-index: 0;
}

.content-container{
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
  position: relative;
  pointer-events: none;
  z-index: 10;
}

/* 新增：白色遮罩动画层 */
.bg-fill {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 24px; /* 与 main-content 圆角一致 */
  clip-path: circle(0% at 100% 100%);
  transition: clip-path 0.8s cubic-bezier(0.25, 0.8, 0.25, 1);
  z-index: 100;           /* 最上层 */
  pointer-events: none; /* 让点击穿透到下层内容 */
}

.reveal-active .bg-fill {
  clip-path: circle(150% at 100% 100%);
  transition-delay: 0s; /* 可根据需要调整 delay */
}

.wave-canvas {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: -1;
}
</style>