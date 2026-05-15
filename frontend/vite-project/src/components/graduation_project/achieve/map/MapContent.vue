<template>
  <div
    class="transactions"
    :class="{ compact: innerCompact }"
    @click="emit('select')"
  >
    <!-- 原有内容（始终渲染，通过透明度隐藏） -->
    <div class="content-wrapper">
        <Map></Map>
      <!-- 新增切换按钮 -->
      <button class="toggle-btn" @click.stop="toggleCompact">
        <span v-if="!innerCompact">💧 切换</span>
        <span v-else>🔁 恢复</span>
      </button>
    </div>

    <!-- 液体破裂动画层（内部紧凑状态显示） -->
    <div v-if="innerCompact" class="liquid-stage" ref="liquidStageRef">
      <div class="shockwave" ref="shockwaveRef"></div>
      <div
        v-for="(drop, idx) in dropConfigs"
        :key="'drop-' + idx"
        :class="['drop', 'drop-' + drop.size]"
        :ref="(el) => setDropRef(el, idx)"
      ></div>
      <div
        v-for="(_, idx) in particleCount"
        :key="'particle-' + idx"
        class="particle"
        :ref="(el) => setParticleRef(el, idx)"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted, nextTick } from 'vue';

import Map from '@/components/graduation_project/achieve/map/Map.vue';

interface Props {
  showHotLabel?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  showHotLabel: false,
});

const emit = defineEmits(['select']);

const transactions = ref([
  { name: '临床医学', price: -21 },
  { name: '计算机科学与技术', price: -35 },
  { name: 'Verizon', price: -61 },
]);

// ---------- 内部控制紧凑状态（与 prop 合并） ----------
const internalCompact = ref(false);
const desiredCompact = computed(() => props.showHotLabel || internalCompact.value);
const innerCompact = ref(desiredCompact.value); // 实际控制模板渲染

function toggleCompact() {
  internalCompact.value = !internalCompact.value;
}

// 液体 DOM 引用
const liquidStageRef = ref<HTMLElement | null>(null);
const shockwaveRef = ref<HTMLElement | null>(null);
const dropRefs = ref<HTMLElement[]>([]);
const particleRefs = ref<HTMLElement[]>([]);

const isBurst = ref(false);
const isAnimating = ref(false);
let currentAnimations: Animation[] = [];
let autoTimer: ReturnType<typeof setTimeout> | null = null;

// 动画参数
const BURST_DURATION = 750;
const PARTICLE_DURATION = 700;
const SHOCKWAVE_DURATION = 550;
const EASING_DROP = 'cubic-bezier(0.22, 0.61, 0.36, 1)';
const EASING_PARTICLE = 'ease-out';
const EASING_SHOCKWAVE = 'ease-out';

const dropConfigs = [
  { size: 'lg', fx: -60, fy: -36 },
  { size: 'lg', fx: 55, fy: -38 },
  { size: 'lg', fx: 5, fy: 65 },
  { size: 'md', fx: -85, fy: 20 },
  { size: 'md', fx: 80, fy: 17 },
  { size: 'md', fx: -35, fy: -75 },
  { size: 'md', fx: 38, fy: -72 },
  { size: 'sm', fx: -65, fy: -63 },
  { size: 'sm', fx: 67, fy: -60 },
  { size: 'sm', fx: -12, fy: 85 },
];

const particleCount = 14;
const particleFlyData = Array.from({ length: particleCount }, (_, i) => {
  const baseAngle = (i / particleCount) * Math.PI * 2;
  const angle = baseAngle + (Math.random() - 0.5) * 0.8;
  const distance = 60 + Math.random() * 80;
  return {
    px: Math.cos(angle) * distance,
    py: Math.sin(angle) * distance,
  };
});

function setDropRef(el: any, idx: number) {
  if (el) dropRefs.value[idx] = el as HTMLElement;
}
function setParticleRef(el: any, idx: number) {
  if (el) particleRefs.value[idx] = el as HTMLElement;
}

// ---------- 关键帧工厂 ----------
function createDropBurstKeyframes(fx: number, fy: number) {
  return [
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(1)', opacity: 0.95 },
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(1.2)', offset: 0.18, opacity: 0.95 },
    { transform: `translate(-50%, -50%) translate(${fx * 0.7}px, ${fy * 0.7}px) scale(1.08)`, offset: 0.45, opacity: 0.85 },
    { transform: `translate(-50%, -50%) translate(${fx}px, ${fy}px) scale(0.92)`, offset: 1, opacity: 0 },
  ];
}

function createParticleBurstKeyframes(px: number, py: number) {
  return [
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(0.2)', opacity: 0 },
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(0.6)', offset: 0.08, opacity: 0.9 },
    { transform: `translate(-50%, -50%) translate(${px * 0.55}px, ${py * 0.55}px) scale(1.3)`, offset: 0.25, opacity: 0.85 },
    { transform: `translate(-50%, -50%) translate(${px * 0.9}px, ${py * 0.9}px) scale(1.6)`, offset: 0.7, opacity: 0.4 },
    { transform: `translate(-50%, -50%) translate(${px}px, ${py}px) scale(0.3)`, offset: 1, opacity: 0 },
  ];
}

function createShockwaveBurstKeyframes() {
  return [
    { transform: 'translate(-50%, -50%) scale(0.3)', opacity: 0.7, borderWidth: '2px' },
    { transform: 'translate(-50%, -50%) scale(6)', offset: 0.4, opacity: 0.4, borderWidth: '1px' },
    { transform: 'translate(-50%, -50%) scale(12)', opacity: 0, borderWidth: '0.5px' },
  ];
}

function createDropAggregateKeyframes(fx: number, fy: number) {
  return [
    { transform: `translate(-50%, -50%) translate(${fx}px, ${fy}px) scale(0.92)`, opacity: 0 },
    { transform: `translate(-50%, -50%) translate(${fx * 0.7}px, ${fy * 0.7}px) scale(1.08)`, offset: 0.55, opacity: 0.85 },
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(1.2)', offset: 0.82, opacity: 0.95 },
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(1)', opacity: 0.95 },
  ];
}

function createParticleAggregateKeyframes(px: number, py: number) {
  return [
    { transform: `translate(-50%, -50%) translate(${px}px, ${py}px) scale(0.3)`, opacity: 0 },
    { transform: `translate(-50%, -50%) translate(${px * 0.9}px, ${py * 0.9}px) scale(1.6)`, offset: 0.3, opacity: 0.4 },
    { transform: `translate(-50%, -50%) translate(${px * 0.55}px, ${py * 0.55}px) scale(1.3)`, offset: 0.75, opacity: 0.85 },
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(0.6)', offset: 0.92, opacity: 0.9 },
    { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(0.2)', opacity: 0 },
  ];
}

function createShockwaveAggregateKeyframes() {
  return [
    { transform: 'translate(-50%, -50%) scale(12)', opacity: 0, borderWidth: '0.5px' },
    { transform: 'translate(-50%, -50%) scale(6)', offset: 0.6, opacity: 0.4, borderWidth: '1px' },
    { transform: 'translate(-50%, -50%) scale(0.3)', offset: 0.9, opacity: 0.7, borderWidth: '2px' },
    { transform: 'translate(-50%, -50%) scale(0)', opacity: 0 },
  ];
}

function cancelAllAnimations() {
  currentAnimations.forEach((anim) => {
    try { anim.cancel(); } catch (_) {}
  });
  currentAnimations = [];
}

async function playBurst() {
  const animations: Animation[] = [];
  dropConfigs.forEach((drop, idx) => {
    const el = dropRefs.value[idx];
    if (!el) return;
    const anim = el.animate(createDropBurstKeyframes(drop.fx, drop.fy), {
      duration: BURST_DURATION,
      easing: EASING_DROP,
      fill: 'forwards',
    });
    animations.push(anim);
  });
  particleFlyData.forEach((data, idx) => {
    const el = particleRefs.value[idx];
    if (!el) return;
    const anim = el.animate(createParticleBurstKeyframes(data.px, data.py), {
      duration: PARTICLE_DURATION,
      easing: EASING_PARTICLE,
      fill: 'forwards',
    });
    animations.push(anim);
  });
  if (shockwaveRef.value) {
    const anim = shockwaveRef.value.animate(createShockwaveBurstKeyframes(), {
      duration: SHOCKWAVE_DURATION,
      easing: EASING_SHOCKWAVE,
      fill: 'forwards',
    });
    animations.push(anim);
  }
  currentAnimations = animations;
  await Promise.all(animations.map((a) => a.finished));
}

async function playAggregate() {
  const animations: Animation[] = [];
  dropConfigs.forEach((drop, idx) => {
    const el = dropRefs.value[idx];
    if (!el) return;
    const anim = el.animate(createDropAggregateKeyframes(drop.fx, drop.fy), {
      duration: BURST_DURATION,
      easing: EASING_DROP,
      fill: 'forwards',
    });
    animations.push(anim);
  });
  particleFlyData.forEach((data, idx) => {
    const el = particleRefs.value[idx];
    if (!el) return;
    const anim = el.animate(createParticleAggregateKeyframes(data.px, data.py), {
      duration: PARTICLE_DURATION,
      easing: EASING_PARTICLE,
      fill: 'forwards',
    });
    animations.push(anim);
  });
  if (shockwaveRef.value) {
    const anim = shockwaveRef.value.animate(createShockwaveAggregateKeyframes(), {
      duration: SHOCKWAVE_DURATION,
      easing: EASING_SHOCKWAVE,
      fill: 'forwards',
    });
    animations.push(anim);
  }
  currentAnimations = animations;
  await Promise.all(animations.map((a) => a.finished));
}

function resetLiquidState() {
  cancelAllAnimations();
  dropRefs.value.forEach((el) => {
    if (el) {
      el.style.transform = 'translate(-50%, -50%) translate(0px, 0px) scale(1)';
      el.style.opacity = '0.95';
    }
  });
  particleRefs.value.forEach((el) => {
    if (el) {
      el.style.transform = 'translate(-50%, -50%) translate(0px, 0px) scale(0)';
      el.style.opacity = '0';
    }
  });
  if (shockwaveRef.value) {
    shockwaveRef.value.style.transform = 'translate(-50%, -50%) scale(0)';
    shockwaveRef.value.style.opacity = '0';
  }
  isBurst.value = false;
  isAnimating.value = false;
}

// 监听组合状态变化，驱动动画和 innerCompact
watch(
  desiredCompact,
  async (newVal, oldVal) => {
    if (oldVal === undefined) {
      // 首次挂载，仅同步渲染状态，不播动画
      if (newVal !== innerCompact.value) {
        innerCompact.value = newVal;
      }
      return;
    }
    if (newVal === oldVal) return;

    if (autoTimer) {
      clearTimeout(autoTimer);
      autoTimer = null;
    }

    if (newVal) {
      // 进入紧凑状态
      innerCompact.value = true;
      await nextTick();
      resetLiquidState();
      autoTimer = setTimeout(async () => {
        if (isAnimating.value) return;
        isAnimating.value = true;
        await playBurst();
        isBurst.value = true;
        isAnimating.value = false;
      }, 200);
    } else {
      // 退出紧凑状态
      if (autoTimer) {
        clearTimeout(autoTimer);
        autoTimer = null;
      }

      if (isBurst.value || isAnimating.value) {
        cancelAllAnimations();
        isAnimating.value = true;
        await playAggregate();
        isBurst.value = false;
        isAnimating.value = false;
      }

      resetLiquidState();
      innerCompact.value = false;
    }
  },
  { immediate: true }
);

onUnmounted(() => {
  if (autoTimer) clearTimeout(autoTimer);
  cancelAllAnimations();
});
</script>

<style scoped>
/* ---------- 卡片容器（截断圆形样式） ---------- */
.transactions {
  width: 760px;
  height: 680px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: box-shadow 0.4s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  border-radius: 0;
  padding: 0;
  background: transparent;
}

.transactions:hover {
  transform: none;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.13);
}

.compact:hover {
  box-shadow: none;
}

/* 截断圆形背景（伪元素） */
.transactions::before {
  content: '';
  position: absolute;
  width: 760px;
  height: 760px;
  border-radius: 50%;
  top: -40px;
  left: 0;
  z-index: 0;
  background: linear-gradient(135deg, #e0e0e0, #f5f5f5, #ffffff);
  box-shadow:
    inset 0 2px 20px rgba(0, 0, 0, 0.04),
    0 6px 24px rgba(0, 0, 0, 0.06);
  clip-path: circle(100% at center);
  transition: clip-path 0.4s ease;
}

.compact::before {
  clip-path: circle(0% at center);
}

.compact {
  box-shadow: none;
}

/* ---------- 内容层 ---------- */
.content-wrapper {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 40px;
  margin-top: 40px;
  transition: opacity 0.4s ease;
  color: #2c3e50;
}

.compact .content-wrapper {
  opacity: 0;
  pointer-events: none;
}

/* ---------- 切换按钮 ---------- */
.toggle-btn {
  margin-top: 28px;
  padding: 12px 28px;
  border: none;
  border-radius: 40px;
  background: linear-gradient(135deg, #d0d0d0, #f0f0f0);
  color: #2c3e50;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.25s ease;
  letter-spacing: 0.5px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.toggle-btn:hover {
  background: linear-gradient(135deg, #c8c8c8, #e8e8e8);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.toggle-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

/* ---------- 液体动画层 ---------- */
.liquid-stage {
  position: absolute;
  inset: 0;
  filter: contrast(16);
  background: transparent;
  z-index: 10;
  overflow: hidden;
}

.transactions.compact .liquid-stage {
  --liquid-color: #ffffff;
  --liquid-color-bright: #f5f5f5;
  --blur-amount: 3.5px;
  --drop-size-lg: 60px;
  --drop-size-md: 40px;
  --drop-size-sm: 24px;
  --particle-size: 8px;
  --shockwave-size: 10px;
}

.drop {
  position: absolute;
  border-radius: 50%;
  background-color: var(--liquid-color);
  filter: blur(var(--blur-amount));
  pointer-events: none;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  will-change: transform, opacity;
}

.drop-lg {
  width: var(--drop-size-lg);
  height: var(--drop-size-lg);
  margin: calc(-1 * var(--drop-size-lg) / 2) 0 0 calc(-1 * var(--drop-size-lg) / 2);
  filter: blur(calc(var(--blur-amount) + 0.5px));
  background-color: var(--liquid-color-bright);
  z-index: 3;
}
.drop-md {
  width: var(--drop-size-md);
  height: var(--drop-size-md);
  margin: calc(-1 * var(--drop-size-md) / 2) 0 0 calc(-1 * var(--drop-size-md) / 2);
  filter: blur(var(--blur-amount));
  z-index: 2;
}
.drop-sm {
  width: var(--drop-size-sm);
  height: var(--drop-size-sm);
  margin: calc(-1 * var(--drop-size-sm) / 2) 0 0 calc(-1 * var(--drop-size-sm) / 2);
  filter: blur(calc(var(--blur-amount) - 0.5px));
  z-index: 1;
}

.drop-lg::after {
  content: '';
  position: absolute;
  top: 14%;
  left: 20%;
  width: 32%;
  height: 28%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.75);
  filter: blur(3px);
  pointer-events: none;
}
.drop-md::after {
  content: '';
  position: absolute;
  top: 12%;
  left: 18%;
  width: 28%;
  height: 24%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.65);
  filter: blur(2px);
  pointer-events: none;
}

.particle {
  position: absolute;
  border-radius: 50%;
  background-color: var(--liquid-color);
  pointer-events: none;
  opacity: 0;
  top: 50%;
  left: 50%;
  width: var(--particle-size);
  height: var(--particle-size);
  margin: calc(-1 * var(--particle-size) / 2) 0 0 calc(-1 * var(--particle-size) / 2);
  filter: blur(2px);
  z-index: 0;
  will-change: transform, opacity;
}

.shockwave {
  position: absolute;
  top: 50%;
  left: 50%;
  width: var(--shockwave-size);
  height: var(--shockwave-size);
  margin: calc(-1 * var(--shockwave-size) / 2) 0 0 calc(-1 * var(--shockwave-size) / 2);
  border-radius: 50%;
  border: 2px solid var(--liquid-color-bright);
  pointer-events: none;
  opacity: 0;
  transform: translate(-50%, -50%) scale(0);
  filter: blur(1.5px);
  z-index: 10;
  will-change: transform, opacity;
}

/* ========== 原有内容样式 ========== */
.transactions h3 {
  font-size: 20px;
  margin-bottom: 24px;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.hot-badge {
  background: #ffecec;
  color: #e5484d;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 16px;
  line-height: 1.2;
}
.t-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 18px;
  text-align: left;
}
.t-icon {
  width: 36px;
  height: 36px;
  background: #f4f6fc;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-dot {
  width: 6px;
  height: 6px;
  background: #333;
  border-radius: 50%;
}
.t-name {
  flex: 1;
  font-size: 15px;
  color: #4a5568;
}
.t-price {
  font-weight: 600;
  color: #1a1a2e;
}
</style>