<template>
  <div class="function-card">
    <div class="card-top">
      <span>Balance</span>
      <span class="visa-logo">VISA</span>
    </div>
    <div class="amount">$ 2200</div>
    <div class="card-bottom">
      <span>Emma Watson</span>
      <div class="chip"></div>
      <button class="action-btn" @click="handleClick">传递</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// 如果你仍需要通过点击切换一个布尔值给父组件，可以保留这个状态
const showFunctionCard = ref(false)

const emit = defineEmits<{
  (e: 'bool-value', value: boolean): void
}>()

function handleClick() {
  // 切换状态并发送事件（不再有任何高度动画或内容展开）
  showFunctionCard.value = !showFunctionCard.value
  emit('bool-value', showFunctionCard.value)
}
</script>

<style scoped>
.function-card {
  background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%);
  width: 280px;
  height: 170px; /* 固定高度，不再变化 */
  border-radius: 24px;
  padding: 20px;
  color: white;
  position: relative;
  box-shadow: 0 20px 40px rgba(255, 107, 107, 0.3);
  /* 移除 transition: height ... 因为高度不再改变 */
  overflow: hidden;
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
  gap: 12px;
}

.chip {
  width: 30px;
  height: 20px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.25);
  border: none;
  color: white;
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.45);
}
</style>

<!--<template>-->
<!--  <div-->
<!--    class="bubble-wrapper"-->
<!--    :style="wrapperStyle"-->
<!--  >-->

<!--    &lt;!&ndash; 交互区域 &ndash;&gt;-->
<!--    <div-->
<!--      ref="boxRef"-->
<!--      class="box"-->
<!--      :style="boxStyle"-->
<!--      :class="{ active: isActive }"-->
<!--      tabindex="0"-->
<!--      role="button"-->
<!--      :aria-label="ariaLabel"-->
<!--      @click="toggle"-->
<!--      @keydown="handleKeydown"-->
<!--      @touchstart.prevent-->
<!--    >-->
<!--      &lt;!&ndash; 上方两个静态水滴（用于粘性融合） &ndash;&gt;-->
<!--      <div class="drop drop-1" />-->
<!--      <div class="drop drop-2" />-->

<!--      &lt;!&ndash; 下方动画水滴：移动 → 变圆 → 膨胀 → 保留 &ndash;&gt;-->
<!--      <div-->
<!--        :key="'drop3-' + animKey"-->
<!--        class="drop drop-3"-->
<!--      />-->

<!--      &lt;!&ndash; 飞溅粒子（同步发生） &ndash;&gt;-->
<!--      <div-->
<!--        v-for="(particle, idx) in particleList"-->
<!--        :key="'particle-' + idx + '-' + animKey"-->
<!--        class="particle"-->
<!--        :style="{-->
<!--          '&#45;&#45;tx': particle.tx + 'px',-->
<!--          '&#45;&#45;ty': particle.ty + 'px',-->
<!--          animationDelay: particle.delay + 's',-->
<!--        }"-->
<!--      />-->
<!--    </div>-->
<!--  </div>-->
<!--</template>-->

<!--<script setup>-->
<!--import { ref, computed, watch } from 'vue'-->

<!--// ==================== Props ====================-->
<!--const props = defineProps({-->
<!--  /** 水滴颜色 */-->
<!--  dropColor: {-->
<!--    type: String,-->
<!--    default: 'black',-->
<!--  },-->
<!--  /** 背景颜色（支持纯色或渐变） */-->
<!--  bgColor: {-->
<!--    type: String,-->
<!--    default: '#ffffff',-->
<!--  },-->
<!--  /** 初始矩形宽度（px） */-->
<!--  rectWidth: {-->
<!--    type: Number,-->
<!--    default: 200,-->
<!--  },-->
<!--  /** 初始矩形高度（px） */-->
<!--  rectHeight: {-->
<!--    type: Number,-->
<!--    default: 140,-->
<!--  },-->
<!--  /** 初始矩形圆角（px） */-->
<!--  rectRadius: {-->
<!--    type: Number,-->
<!--    default: 8,-->
<!--  },-->
<!--  /** 膨胀后圆形尺寸（px） */-->
<!--  circleSize: {-->
<!--    type: Number,-->
<!--    default: 60,-->
<!--  },-->
<!--  /** 模糊量（px） */-->
<!--  blurAmount: {-->
<!--    type: Number,-->
<!--    default: 15,-->
<!--  },-->
<!--  /** 对比度级别 */-->
<!--  contrastLevel: {-->
<!--    type: Number,-->
<!--    default: 30,-->
<!--  },-->
<!--  /** 初始是否激活 */-->
<!--  modelValue: {-->
<!--    type: Boolean,-->
<!--    default: false,-->
<!--  },-->
<!--  /** 粒子数量 */-->
<!--  particleCount: {-->
<!--    type: Number,-->
<!--    default: 16,-->
<!--  },-->
<!--})-->

<!--// ==================== Emits ====================-->
<!--const emit = defineEmits(['update:modelValue', 'toggle'])-->

<!--// ==================== State ====================-->
<!--const isActive = ref(props.modelValue)-->
<!--const animKey = ref(0)-->
<!--const boxRef = ref(null)-->

<!--// 监听外部 modelValue 变化-->
<!--watch(-->
<!--  () => props.modelValue,-->
<!--  (val) => {-->
<!--    if (val !== isActive.value) {-->
<!--      isActive.value = val-->
<!--      animKey.value++-->
<!--    }-->
<!--  }-->
<!--)-->

<!--// ==================== Computed ====================-->
<!--/** 当前提示文字 */-->
<!--const currentHint = computed(() => {-->
<!--  return isActive.value ? props.activeHint : props.inactiveHint-->
<!--})-->

<!--/** Box 内联样式（CSS 变量） */-->
<!--const boxStyle = computed(() => ({-->
<!--  '&#45;&#45;drop-color': props.dropColor,-->
<!--  '&#45;&#45;bg': props.bgColor,-->
<!--  '&#45;&#45;rect-width': props.rectWidth + 'px',-->
<!--  '&#45;&#45;rect-height': props.rectHeight + 'px',-->
<!--  '&#45;&#45;rect-radius': props.rectRadius + 'px',-->
<!--  '&#45;&#45;circle-size': props.circleSize + 'px',-->
<!--  '&#45;&#45;blur-amount': props.blurAmount + 'px',-->
<!--  '&#45;&#45;contrast-level': props.contrastLevel,-->
<!--  // 使用 background 而不是 backgroundColor，以支持渐变等复杂值-->
<!--  background: props.bgColor,-->
<!--  filter: `contrast(${props.contrastLevel})`,-->
<!--}))-->

<!--/** Wrapper 样式 */-->
<!--const wrapperStyle = computed(() => ({-->
<!--  '&#45;&#45;bg': props.bgColor,-->
<!--}))-->

<!--/** 粒子列表（同步喷溅：延迟极短，与水滴移动同时开始） */-->
<!--const particleList = computed(() => {-->
<!--  const seed = animKey.value-->
<!--  const list = []-->
<!--  for (let i = 0; i < props.particleCount; i++) {-->
<!--    const seedOffset = ((seed * 137 + i * 73) % 100) / 100-->
<!--    const angle = (i / props.particleCount) * Math.PI * 2 + seedOffset * 0.5-->
<!--    // 缩短飞溅距离，让粒子更贴合分离瞬间-->
<!--    const distance = 40 + seedOffset * 40-->
<!--    const tx = Math.cos(angle) * distance-->
<!--    const ty = Math.sin(angle) * distance + 100  // 向下偏移减少，保持视觉集中-->
<!--    // 延迟从0开始，依次微增，全部在0.2秒内开始-->
<!--    const delay = i * 0.03-->
<!--    list.push({ tx, ty, delay })-->
<!--  }-->
<!--  return list-->
<!--})-->

<!--// ==================== Methods ====================-->
<!--function toggle() {-->
<!--  const newVal = !isActive.value-->
<!--  isActive.value = newVal-->
<!--  animKey.value++-->
<!--  emit('update:modelValue', newVal)-->
<!--  emit('toggle', newVal)-->
<!--}-->

<!--function handleKeydown(e) {-->
<!--  if (e.key === 'Enter' || e.key === ' ') {-->
<!--    e.preventDefault()-->
<!--    toggle()-->
<!--  }-->
<!--}-->

<!--// ==================== Expose ====================-->
<!--defineExpose({-->
<!--  /** 程序化切换 */-->
<!--  toggle,-->
<!--  /** 当前激活状态 */-->
<!--  isActive,-->
<!--  /** box DOM 引用 */-->
<!--  boxRef,-->
<!--})-->
<!--</script>-->

<!--<style scoped>-->
<!--/* ==================== 变量默认值 ==================== */-->
<!--.bubble-wrapper {-->
<!--  &#45;&#45;drop-color: white;-->
<!--  &#45;&#45;bg: #111;-->
<!--  &#45;&#45;rect-width: 160px;-->
<!--  &#45;&#45;rect-height: 100px;-->
<!--  &#45;&#45;rect-radius: 25px;-->
<!--  &#45;&#45;circle-size: 100px;-->
<!--  &#45;&#45;blur-amount: 15px;-->
<!--  &#45;&#45;contrast-level: 30;-->

<!--  position: relative;-->
<!--  width: 100%;-->
<!--  height: 100%;-->
<!--  min-height: 420px;-->
<!--  display: flex;-->
<!--  justify-content: center;-->
<!--  align-items: center;-->
<!--  background-color: #0a0a0a;-->
<!--  overflow: hidden;-->
<!--  user-select: none;-->
<!--  font-family: 'Segoe UI', system-ui, sans-serif;-->
<!--}-->

<!--/* ==================== 提示文字 ==================== */-->
<!--.hint {-->
<!--  position: absolute;-->
<!--  top: 8%;-->
<!--  left: 50%;-->
<!--  transform: translateX(-50%);-->
<!--  color: rgba(255, 255, 255, 0.7);-->
<!--  font-size: 1rem;-->
<!--  letter-spacing: 0.12em;-->
<!--  pointer-events: none;-->
<!--  z-index: 10;-->
<!--  transition: opacity 0.5s;-->
<!--  text-align: center;-->
<!--  white-space: nowrap;-->
<!--}-->

<!--/* ==================== 交互盒子 ==================== */-->
<!--.box {-->
<!--  position: relative;-->
<!--  width: 100%;-->
<!--  height: 100%;-->
<!--  display: flex;-->
<!--  justify-content: center;-->
<!--  align-items: center;-->
<!--  cursor: pointer;-->
<!--  transition: background-color 0.3s;-->
<!--  outline: none;-->
<!--}-->

<!--.box:focus-visible {-->
<!--  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.5) inset;-->
<!--}-->

<!--/* ==================== 水滴通用样式 ==================== */-->
<!--.drop {-->
<!--  width: var(&#45;&#45;rect-width);-->
<!--  height: var(&#45;&#45;rect-height);-->
<!--  border-radius: var(&#45;&#45;rect-radius);-->
<!--  background-color: var(&#45;&#45;drop-color);-->
<!--  position: absolute;-->
<!--  top: 50%;-->
<!--  left: 50%;-->
<!--  margin-top: calc(-1 * var(&#45;&#45;rect-height) / 2);-->
<!--  margin-left: calc(-1 * var(&#45;&#45;rect-width) / 2);-->
<!--  filter: blur(var(&#45;&#45;blur-amount));-->
<!--  transition:-->
<!--    transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1),-->
<!--    border-radius 0.6s cubic-bezier(0.34, 1.56, 0.64, 1),-->
<!--    width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1),-->
<!--    height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1),-->
<!--    margin 0.6s cubic-bezier(0.34, 1.56, 0.64, 1),-->
<!--    opacity 0.3s ease;-->
<!--  pointer-events: none;-->
<!--}-->

<!--/* 高光 */-->
<!--.drop::after {-->
<!--  content: '';-->
<!--  position: absolute;-->
<!--  top: 15%;-->
<!--  left: 20%;-->
<!--  width: 30%;-->
<!--  height: 30%;-->
<!--  border-radius: 50%;-->
<!--  background: rgba(255, 255, 255, 0.55);-->
<!--  filter: blur(4px);-->
<!--  pointer-events: none;-->
<!--}-->

<!--/* ==================== 激活状态：上方水滴保持不动 ==================== */-->
<!--.box.active .drop-1,-->
<!--.box.active .drop-2 {-->
<!--  transform: translateY(0);-->
<!--}-->

<!--/* ==================== 激活状态：下方水滴执行动画 ==================== */-->
<!--.box.active .drop-3 {-->
<!--  animation: moveAndStay 1s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;-->
<!--}-->

<!--/* ==================== 关键帧：移动 → 变圆 → 膨胀 → 保留 ==================== */-->
<!--@keyframes moveAndStay {-->
<!--  0% {-->
<!--    transform: translateY(0);-->
<!--    border-radius: var(&#45;&#45;rect-radius);-->
<!--    width: var(&#45;&#45;rect-width);-->
<!--    height: var(&#45;&#45;rect-height);-->
<!--    margin-top: calc(-1 * var(&#45;&#45;rect-height) / 2);-->
<!--    margin-left: calc(-1 * var(&#45;&#45;rect-width) / 2);-->
<!--    opacity: 1;-->
<!--  }-->
<!--  40% {-->
<!--    transform: translateY(150px);-->
<!--    border-radius: 50%;-->
<!--    width: var(&#45;&#45;circle-size);-->
<!--    height: var(&#45;&#45;circle-size);-->
<!--    margin-top: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--    margin-left: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--    opacity: 1;-->
<!--  }-->
<!--  70% {-->
<!--    transform: translateY(180px) scale(1.2);-->
<!--    border-radius: 50%;-->
<!--    width: var(&#45;&#45;circle-size);-->
<!--    height: var(&#45;&#45;circle-size);-->
<!--    margin-top: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--    margin-left: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--    opacity: 1;-->
<!--  }-->
<!--  100% {-->
<!--    transform: translateY(180px) scale(1);-->
<!--    border-radius: 50%;-->
<!--    width: var(&#45;&#45;circle-size);-->
<!--    height: var(&#45;&#45;circle-size);-->
<!--    margin-top: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--    margin-left: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--    opacity: 1;-->
<!--  }-->
<!--}-->

<!--/* ==================== 粒子 ==================== */-->
<!--.particle {-->
<!--  position: absolute;-->
<!--  top: 50%;-->
<!--  left: 50%;-->
<!--  width: 20px;-->
<!--  height: 20px;-->
<!--  border-radius: 50%;-->
<!--  background-color: var(&#45;&#45;drop-color);-->
<!--  filter: blur(8px);-->
<!--  pointer-events: none;-->
<!--  opacity: 0;-->
<!--}-->

<!--.box.active .particle {-->
<!--  animation: particleFly 0.6s ease-out forwards;-->
<!--}-->

<!--@keyframes particleFly {-->
<!--  0% {-->
<!--    opacity: 0;-->
<!--    transform: translate(0, 0) scale(0.3);-->
<!--  }-->
<!--  30% {-->
<!--    opacity: 0.9;-->
<!--  }-->
<!--  100% {-->
<!--    opacity: 0;-->
<!--    transform: translate(var(&#45;&#45;tx), var(&#45;&#45;ty)) scale(1.2);-->
<!--  }-->
<!--}-->

<!--/* ==================== 移动端适配 ==================== */-->
<!--@media (max-width: 600px) {-->
<!--  .bubble-wrapper {-->
<!--    min-height: 340px;-->
<!--  }-->

<!--  .drop {-->
<!--    &#45;&#45;rect-width: 110px;-->
<!--    &#45;&#45;rect-height: 70px;-->
<!--    &#45;&#45;rect-radius: 18px;-->
<!--    &#45;&#45;circle-size: 70px;-->
<!--    width: var(&#45;&#45;rect-width);-->
<!--    height: var(&#45;&#45;rect-height);-->
<!--    border-radius: var(&#45;&#45;rect-radius);-->
<!--    margin-top: calc(-1 * var(&#45;&#45;rect-height) / 2);-->
<!--    margin-left: calc(-1 * var(&#45;&#45;rect-width) / 2);-->
<!--    filter: blur(10px);-->
<!--  }-->

<!--  /* 移动端需要重新定义 keyframes（因为 translateY 距离不同） */-->
<!--  @keyframes moveAndStay {-->
<!--    0% {-->
<!--      transform: translateY(0);-->
<!--      border-radius: var(&#45;&#45;rect-radius);-->
<!--      width: var(&#45;&#45;rect-width);-->
<!--      height: var(&#45;&#45;rect-height);-->
<!--      margin-top: calc(-1 * var(&#45;&#45;rect-height) / 2);-->
<!--      margin-left: calc(-1 * var(&#45;&#45;rect-width) / 2);-->
<!--      opacity: 1;-->
<!--    }-->
<!--    40% {-->
<!--      transform: translateY(100px);-->
<!--      border-radius: 50%;-->
<!--      width: var(&#45;&#45;circle-size);-->
<!--      height: var(&#45;&#45;circle-size);-->
<!--      margin-top: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--      margin-left: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--      opacity: 1;-->
<!--    }-->
<!--    70% {-->
<!--      transform: translateY(120px) scale(1.2);-->
<!--      border-radius: 50%;-->
<!--      width: var(&#45;&#45;circle-size);-->
<!--      height: var(&#45;&#45;circle-size);-->
<!--      margin-top: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--      margin-left: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--      opacity: 1;-->
<!--    }-->
<!--    100% {-->
<!--      transform: translateY(120px) scale(1);-->
<!--      border-radius: 50%;-->
<!--      width: var(&#45;&#45;circle-size);-->
<!--      height: var(&#45;&#45;circle-size);-->
<!--      margin-top: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--      margin-left: calc(-1 * var(&#45;&#45;circle-size) / 2);-->
<!--      opacity: 1;-->
<!--    }-->
<!--  }-->

<!--  .hint {-->
<!--    font-size: 0.85rem;-->
<!--  }-->
<!--}-->
<!--</style>-->