<template>
  <div class="transactions" :class="{ compact: innerCompact }">
    <!-- 原有内容（始终渲染，通过透明度隐藏） -->
    <div class="content-wrapper">
      <h3>
        热门专业
        <span class="hot-badge">热门</span>
      </h3>
      <div class="transaction-list">
        <div v-for="(t, i) in transactions" :key="i" class="t-item">
          <div class="t-icon"><span class="icon-dot"></span></div>
          <span class="t-name">{{ t.name }}</span>
          <span class="t-price">{{ t.price }}</span>
        </div>
      </div>
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
import { ref, watch, onUnmounted, nextTick } from 'vue';

interface Props {
  showHotLabel?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  showHotLabel: false,
});

const transactions = ref([
  { name: 'Starbucks', price: -21 },
  { name: 'Apple Store', price: -35 },
  { name: 'Verizon', price: -61 },
]);

// ---------- 内部控制紧凑状态 ----------
const innerCompact = ref(props.showHotLabel);

// 液体 DOM 引用
const liquidStageRef = ref<HTMLElement | null>(null);
const shockwaveRef = ref<HTMLElement | null>(null);
const dropRefs = ref<HTMLElement[]>([]);
const particleRefs = ref<HTMLElement[]>([]);

const isBurst = ref(false);
const isAnimating = ref(false);
let currentAnimations: Animation[] = [];
let autoTimer: ReturnType<typeof setTimeout> | null = null;

// 动画参数（60px 液滴，适配 300px 卡片）
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
// 正向破裂关键帧
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

// 逆向聚合关键帧（从最终破裂状态回到初始聚合状态）
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
    { transform: 'translate(-50%, -50%) scale(0)', opacity: 0 }, // 最终消失
  ];
}

// ---------- 动画播放 ----------
// 清空当前动画
function cancelAllAnimations() {
  currentAnimations.forEach((anim) => {
    try { anim.cancel(); } catch (_) {}
  });
  currentAnimations = [];
}

// 播放破裂动画（正向）
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

// 播放聚合动画（逆向）
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

// 重置到聚合状态（无动画，用于紧急回退）
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

// ---------- 监听外部 prop 变化 ----------
watch(
  () => props.showHotLabel,
  async (val) => {
    // 清除自动破裂定时器
    if (autoTimer) {
      clearTimeout(autoTimer);
      autoTimer = null;
    }

    if (val) {
      // 显示液体层
      innerCompact.value = true;
      // 等待 DOM 渲染
      await nextTick();
      // 重置液体到初始聚合状态
      resetLiquidState();

      // 0.2 秒后自动破裂
      autoTimer = setTimeout(async () => {
        if (isAnimating.value) return;
        isAnimating.value = true;
        await playBurst();
        isBurst.value = true;
        isAnimating.value = false;
      }, 200);
    } else {
      // 关闭液体层：先逆向聚合，再隐藏
      if (autoTimer) {
        clearTimeout(autoTimer);
        autoTimer = null;
      }

      // 如果正在破裂动画中或已经完成破裂，播放聚合动画
      if (isBurst.value || isAnimating.value) {
        // 取消当前正向动画，防止冲突
        cancelAllAnimations();
        // 确保元素停留在破裂后的状态（通过内联样式模拟？但聚合动画会覆盖）
        // 直接播放聚合动画，它会从当前视觉状态开始（因为关键帧已定义好终点）
        isAnimating.value = true;
        await playAggregate();
        isBurst.value = false;
        isAnimating.value = false;
      }

      // 聚合完成后（或本就不需要聚合），重置并隐藏
      resetLiquidState();
      innerCompact.value = false; // 移除紧凑类，内容淡入，背景展开
    }
  }
);

onUnmounted(() => {
  if (autoTimer) clearTimeout(autoTimer);
  cancelAllAnimations();
});
</script>

<style scoped>
/* ---------- 卡片容器（背景由伪元素实现） ---------- */
.transactions {
  width: 300px;
  background: transparent;
  border-radius: 24px;
  padding: 3px 24px;
  height: fit-content;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.4s ease;
}

/* 伪元素模拟白色背景，通过 clip-path 实现从四周向中心消失/出现 */
.transactions::before {
  content: '';
  position: absolute;
  inset: 0;
  background: white;
  border-radius: inherit;
  z-index: 0;
  clip-path: circle(100% at center);
  transition: clip-path 0.4s ease;
}

.compact::before {
  clip-path: circle(0% at center);
}

.compact {
  box-shadow: none;
}

/* 内容层在伪元素上方 */
.content-wrapper {
  position: relative;
  z-index: 1;
  transition: opacity 0.4s ease;
}
.compact .content-wrapper {
  opacity: 0;
  pointer-events: none;
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

/* 液体元素变量（60px 级别） */
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

/* 基础液滴 */
.drop {
  position: absolute;
  border-radius: 50%;
  background-color: var(--liquid-color);
  filter: blur(var(--blur-amount));
  pointer-events: none;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) translate(0px, 0px);
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

/* 高光 */
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

/* 粒子 */
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

/* 冲击波 */
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
  font-size: 18px;
  margin-bottom: 20px;
  color: #333;
  display: flex;
  align-items: center;
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
  margin-bottom: 15px;
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
  font-size: 14px;
  color: #555;
}
.t-price {
  font-weight: 600;
  color: #333;
}
</style>