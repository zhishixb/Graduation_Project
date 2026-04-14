<template>
  <div class="achieve-container">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar">
      <div class="logo-area">
        <div class="logo-content">
          <div class="logo-icon">C</div>
          <span class="logo-text">CBANK</span>
        </div>
        <div class="header-actions">
          <div class="menu-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
          </div>
          <div class="profile-pic">
            <img src="https://i.pravatar.cc/150?img=32" alt="Profile" />
          </div>
        </div>
      </div>

      <!-- 两个级联选择器卡片 -->
      <div class="balance-cards">
        <MajorCascader />
        <JobCascader />
      </div>

      <div class="services-section">
        <h4>Services</h4>
        <div class="services-grid">
          <div class="service-item" @click="triggerRightExpand">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
            Insurance
          </div>
          <div class="service-item"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>Payments</div>
          <div class="service-item"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M6 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M9 18h6"/></svg>Utility</div>
          <div class="service-item"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>Transfer</div>
        </div>
      </div>

      <div class="bottom-icons">
        <div class="icon-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1Z"/></svg></div>
        <div class="icon-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div>
        <div class="icon-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg></div>
      </div>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="main-content">
      <canvas ref="waveCanvas" class="wave-canvas"></canvas>

      <!-- 扩散层（圆形色块） -->
      <div
        v-if="showRipple"
        class="ripple-expand"
        :class="{ active: rippleActive }"
        :style="{ backgroundColor: rippleColor, left: rippleCenter.x + 'px', top: rippleCenter.y + 'px' }"
      ></div>

      <!-- 使用 n-tabs 替代原来的顶部导航 -->
      <n-tabs v-model:value="activeTab" class="custom-tabs" @update:value="onTabChange">
        <n-tab-pane name="dashboard" tab="Dashboard">
          <div :class="['tab-content', { 'fade-out': isFadingOut }]">
            <div class="content-area">
              <div class="left-column">
                <div class="credit-card">
                  <div class="card-top">
                    <span>Balance</span>
                    <span class="visa-logo">VISA</span>
                  </div>
                  <div class="amount">$ 2200</div>
                  <div class="card-bottom">
                    <span>Emma Watson</span>
                    <div class="chip"></div>
                  </div>
                </div>
                <HotMajors />
              </div>
              <div class="right-column">
                <Bubble
                  color="purple"
                  top="0"
                  right="100px"
                  width="110px"
                  height="110px"
                  title="Discounts"
                  value="$ 1392"
                />
                <Bubble
                  color="blue"
                  top="100px"
                  right="180px"
                  width="90px"
                  height="90px"
                  title="地区分布"
                  :icon="EarthOutline"
                />
                <Bubble
                  color="orange"
                  top="120px"
                  right="70px"
                  width="100px"
                  height="100px"
                  title="Yours"
                  value="$ 1280"
                />
                <MatchScores class="absolute-match" />
              </div>
            </div>
          </div>
        </n-tab-pane>

        <n-tab-pane name="expenses" tab="Expenses">
          <div :class="['tab-content', { 'fade-out': isFadingOut }]">
            <div class="placeholder-content">
              <h2>Expenses Content</h2>
              <p>这里展示支出相关数据...</p>
            </div>
          </div>
        </n-tab-pane>

        <n-tab-pane name="history" tab="History">
          <div :class="['tab-content', { 'fade-out': isFadingOut }]">
            <div class="placeholder-content">
              <h2>History Content</h2>
              <p>这里展示历史记录...</p>
            </div>
          </div>
        </n-tab-pane>

        <n-tab-pane name="actions" tab="Actions">
          <div :class="['tab-content', { 'fade-out': isFadingOut }]">
            <div class="placeholder-content">
              <h2>Actions Content</h2>
              <p>这里展示操作选项...</p>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { EarthOutline } from '@vicons/ionicons5';
import { NTabs, NTabPane } from 'naive-ui';
import HotMajors from '@/components/graduation_project/achieve/HotMajors.vue';
import MatchScores from '@/components/graduation_project/achieve/MatchScores.vue';
import Bubble from '@/components/graduation_project/achieve/Bubble.vue';
import JobCascader from '@/components/graduation_project/achieve/left_card/JobCascader.vue';
import MajorCascader from '@/components/graduation_project/achieve/left_card/MajorCascader.vue';

// ==================== 标签页状态 ====================
const activeTab = ref('dashboard');

// ==================== 扩散效果相关状态 ====================
const isFadingOut = ref(false);
const showRipple = ref(false);
const rippleActive = ref(false);
const rippleColor = ref('#FF6B6B');
const rippleCenter = ref({ x: 0, y: 0 });

function getRightCenter() {
  const main = document.querySelector('.main-content') as HTMLElement;
  if (!main) return { x: 0, y: 0 };
  const rect = main.getBoundingClientRect();
  return { x: rect.width / 2, y: rect.height / 2 };
}

function triggerRightExpand() {
  if (isFadingOut.value) return;
  rippleCenter.value = getRightCenter();
  isFadingOut.value = true;
  setTimeout(() => {
    showRipple.value = true;
    rippleColor.value = '#FF6B6B';
    nextTick(() => {
      rippleActive.value = true;
    });
  }, 200);
  setTimeout(() => {
    if (showRipple.value) {
      rippleColor.value = '#4CAF50';
      setTimeout(() => {
        if (showRipple.value) {
          rippleActive.value = false;
          setTimeout(() => {
            showRipple.value = false;
            isFadingOut.value = false;
          }, 500);
        }
      }, 300);
    }
  }, 600);
}

function onTabChange(tabName: string) {
  console.log('切换到标签页:', tabName);
}

// ==================== 波浪画布逻辑 ====================
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
  width: 980px;
  height: 560px;
  background-color: #F4F6FC;
  border-radius: 30px;
  display: flex;
  flex-direction: row;
  padding: 24px;
  gap: 24px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.05);
}

/* 侧边栏样式 */
.sidebar {
  width: 260px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 10px;
  z-index: 10;
}

.logo-area {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.logo-content {
  display: flex;
  align-items: center;
  font-weight: 700;
  font-size: 18px;
  color: #333;
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
  margin-right: 10px;
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
  margin-bottom: 16px;
  color: #333;
  font-size: 16px;
}

.services-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.service-item {
  background: white;
  height: 80px;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.02);
}

.service-item:hover {
  transform: translateY(-2px);
}

.bottom-icons {
  display: flex;
  justify-content: space-around;
}

.icon-item {
  width: 40px;
  height: 40px;
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
  overflow: visible;  /* 原为 hidden，改为 visible */
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
  z-index: 0;
}

/* 扩散圆层样式 */
.ripple-expand {
  position: absolute;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  transform: translate(-50%, -50%) scale(0);
  transition: transform 0.6s cubic-bezier(0.2, 0.9, 0.4, 1.1), background-color 0.3s ease;
  z-index: 20;
  pointer-events: none;
  will-change: transform;
  opacity: 0.95;
}

.ripple-expand.active {
  transform: translate(-50%, -50%) scale(20);
}

/* n-tabs 自定义样式，与原来的 top-nav 风格一致 */
.custom-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.custom-tabs :deep(.n-tabs-nav) {
  background: transparent;
  border-bottom: none;
  margin-bottom: 30px;
}
.custom-tabs :deep(.n-tabs-tab) {
  font-size: 15px;
  font-weight: 500;
  color: #888;
  padding: 0 0 4px 0;
  margin-right: 20px;
  background: transparent;
}
.custom-tabs :deep(.n-tabs-tab--active) {
  color: #333;
  border-bottom: 2px solid #333;
}
.custom-tabs :deep(.n-tabs-tab__label) {
  padding: 0;
}
.custom-tabs :deep(.n-tabs-nav-scroll-content) {
  justify-content: flex-start;
}
.custom-tabs :deep(.n-tabs-bar) {
  display: none;
}
.custom-tabs :deep(.n-tabs-pane-wrapper) {
  flex: 1;
  overflow: auto;
}

/* 标签页内容容器 */
.tab-content {
  width: 100%;
  height: 100%;
  transition: opacity 0.3s ease;
}
.tab-content.fade-out {
  opacity: 0;
  pointer-events: none;
}

/* 原有 .content-area 样式，保持在 Dashboard 内部 */
.content-area {
  display: flex;
  justify-content: space-between;
  height: 100%;
}

.left-column {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 55%;
}

.credit-card {
  margin-top: 20px;
  background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%);
  width: 280px;
  height: 170px;
  border-radius: 24px;
  padding: 20px;
  color: white;
  position: relative;
  box-shadow: 0 20px 40px rgba(255, 107, 107, 0.3);
}

.card-top {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  opacity: 0.9;
}

.amount {
  font-size: 32px;
  font-weight: 700;
  margin: 15px 0;
}

.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  font-size: 12px;
}

.chip {
  width: 30px;
  height: 20px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.right-column {
  width: 40%;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-top: 20px;
}

/* MatchScores 绝对定位调整 */
.absolute-match {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 290px;
  z-index: 10;
}

/* 其他标签页占位样式 */
.placeholder-content {
  background: white;
  border-radius: 24px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.placeholder-content h2 {
  color: #333;
  margin-bottom: 16px;
}
.placeholder-content p {
  color: #888;
}
</style>