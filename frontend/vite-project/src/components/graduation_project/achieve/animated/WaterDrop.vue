<template>
    <div class="liquid-container">
        <div
            class="liquid-stage"
            ref="liquidStageRef"
            role="button"
            tabindex="0"
            aria-label="点击触发液体破裂，再次点击逆向聚合"
            @click.stop="handleClick"
            @keydown="handleKeydown"
            @touchstart.prevent="handleClick"
        >
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

<script setup>
import { ref, onUnmounted } from 'vue';

const liquidStageRef = ref(null);
const shockwaveRef = ref(null);
const dropRefs = ref([]);
const particleRefs = ref([]);

const isBurst = ref(false);
const isAnimating = ref(false);
let currentAnimations = [];

const BURST_DURATION = 750;
const PARTICLE_DURATION = 700;
const SHOCKWAVE_DURATION = 550;
const EASING_DROP = 'cubic-bezier(0.22, 0.61, 0.36, 1)';
const EASING_PARTICLE = 'ease-out';
const EASING_SHOCKWAVE = 'ease-out';

// 液滴偏移量（适配60px大液滴，全部在324x233容器内）
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
// 粒子飞行距离大幅增强
const particleFlyData = Array.from({ length: particleCount }, (_, i) => {
    const baseAngle = (i / particleCount) * Math.PI * 2;
    const angle = baseAngle + (Math.random() - 0.5) * 0.8;
    const distance = 60 + Math.random() * 80; // 范围60~140
    return {
        px: Math.cos(angle) * distance,
        py: Math.sin(angle) * distance,
    };
});

function setDropRef(el, idx) {
    if (el) dropRefs.value[idx] = el;
}
function setParticleRef(el, idx) {
    if (el) particleRefs.value[idx] = el;
}

function createDropKeyframes(fx, fy) {
    return [
        { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(1)', opacity: 0.95 },
        { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(1.2)', offset: 0.18, opacity: 0.95 },
        { transform: `translate(-50%, -50%) translate(${fx * 0.7}px, ${fy * 0.7}px) scale(1.08)`, offset: 0.45, opacity: 0.85 },
        { transform: `translate(-50%, -50%) translate(${fx}px, ${fy}px) scale(0.92)`, offset: 1, opacity: 0 },
    ];
}

function createParticleKeyframes(px, py) {
    return [
        { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(0.2)', opacity: 0 },
        { transform: 'translate(-50%, -50%) translate(0px, 0px) scale(0.6)', offset: 0.08, opacity: 0.9 },
        { transform: `translate(-50%, -50%) translate(${px * 0.55}px, ${py * 0.55}px) scale(1.3)`, offset: 0.25, opacity: 0.85 },
        { transform: `translate(-50%, -50%) translate(${px * 0.9}px, ${py * 0.9}px) scale(1.6)`, offset: 0.7, opacity: 0.4 },
        { transform: `translate(-50%, -50%) translate(${px}px, ${py}px) scale(0.3)`, offset: 1, opacity: 0 },
    ];
}

function createShockwaveKeyframes() {
    return [
        { transform: 'translate(-50%, -50%) scale(0.3)', opacity: 0.7, borderWidth: '2px' },
        { transform: 'translate(-50%, -50%) scale(6)', offset: 0.4, opacity: 0.4, borderWidth: '1px' },
        { transform: 'translate(-50%, -50%) scale(12)', opacity: 0, borderWidth: '0.5px' },
    ];
}

async function playBurst() {
    const animations = [];
    dropConfigs.forEach((drop, idx) => {
        const el = dropRefs.value[idx];
        if (!el) return;
        const anim = el.animate(createDropKeyframes(drop.fx, drop.fy), {
            duration: BURST_DURATION,
            easing: EASING_DROP,
            fill: 'forwards',
        });
        animations.push(anim);
    });
    particleFlyData.forEach((data, idx) => {
        const el = particleRefs.value[idx];
        if (!el) return;
        const anim = el.animate(createParticleKeyframes(data.px, data.py), {
            duration: PARTICLE_DURATION,
            easing: EASING_PARTICLE,
            fill: 'forwards',
        });
        animations.push(anim);
    });
    if (shockwaveRef.value) {
        const anim = shockwaveRef.value.animate(createShockwaveKeyframes(), {
            duration: SHOCKWAVE_DURATION,
            easing: EASING_SHOCKWAVE,
            fill: 'forwards',
        });
        animations.push(anim);
    }
    currentAnimations = animations;
    await Promise.all(animations.map(a => a.finished));
}

async function playReverse() {
    currentAnimations.forEach(anim => anim.reverse());
    await Promise.all(currentAnimations.map(a => a.finished));
    currentAnimations = [];
}

async function handleClick() {
    if (isAnimating.value) return;
    isAnimating.value = true;
    if (!isBurst.value) {
        await playBurst();
        isBurst.value = true;
    } else {
        await playReverse();
        isBurst.value = false;
    }
    isAnimating.value = false;
}

function handleKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleClick();
    }
}

onUnmounted(() => {
    currentAnimations.forEach(anim => {
        try { anim.cancel(); } catch (_) {}
    });
    currentAnimations = [];
});
</script>

<style scoped>
.liquid-container {
    /* 纯白液体，60px 级大液滴 */
    --liquid-color: #ffffff;
    --liquid-color-bright: #f5f5f5;
    --blur-amount: 3.5px;
    --contrast-level: 16;
    --drop-size-lg: 60px;
    --drop-size-md: 40px;
    --drop-size-sm: 24px;
    --particle-size: 8px;
    --shockwave-size: 10px;

    width: 324px;
    height: 233px;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    background: transparent;
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    font-family: 'Segoe UI', system-ui, sans-serif;
}

.liquid-stage {
    position: absolute;
    inset: 0;
    filter: contrast(var(--contrast-level));
    background: transparent;
    cursor: pointer;
    z-index: 1;
    overflow: hidden;
}

/* 液滴基础 */
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

@media (max-width: 324px) {
    .liquid-container {
        width: 100%;
        height: auto;
        aspect-ratio: 324 / 233;
    }
}
</style>