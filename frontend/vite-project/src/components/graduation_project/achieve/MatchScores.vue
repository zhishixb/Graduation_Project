  <template>
    <div class="match-scores" :class="{ 'reveal-active': showReveal }">
      <!-- 从左向右填充的背景层 -->
      <div class="bg-fill"></div>

      <!-- 包裹实际内容的层（用于淡入） -->
      <div class="content-wrapper" :class="{ 'fade-in': showReveal }">
        <h3 v-if="showTitle">{{ title }}</h3>
        <div class="bars-container">
          <div v-for="(score, idx) in scores" :key="idx" class="bar-item">
            <div class="bar-wrapper">
              <div
                class="bar"
                :style="{
                  height: score * 100 + '%',
                  background: barColors[idx]
                }"
              ></div>
            </div>
            <span class="score-value">{{ score.toFixed(2) }}</span>
            <span class="bar-label">{{ labels[idx] }}</span>
          </div>
        </div>
      </div>
    </div>
  </template>

  <script setup lang="ts">
  import { ref, watch, onBeforeUnmount } from 'vue';

  // ---------- Props ----------
  const props = withDefaults(defineProps<{
    showTitle?: boolean; // 控制标题显隐（之前的 prop）
    reveal?: boolean;    // 接收父组件传递的布尔值，触发动画
  }>(), {
    showTitle: true,
    reveal: false,
  });

  // ---------- 内部状态 ----------
  const title = '匹配分数';
  const scores = ref([0.65, 0.82, 0.43, 0.91, 0.57, 0.73, 0.38]);
  const labels = ['维度A', '维度B', '维度C', '维度D', '维度E', '维度F', '维度G'];
  const barColors = [
    'linear-gradient(180deg, #6C5CE7, #a29bfe)',
    'linear-gradient(180deg, #0984E3, #74B9FF)',
    'linear-gradient(180deg, #00B894, #55EFC4)',
    'linear-gradient(180deg, #FDCB6E, #FFEAA7)',
    'linear-gradient(180deg, #E17055, #FF7675)',
    'linear-gradient(180deg, #D63031, #FF7675)',
    'linear-gradient(180deg, #6C5CE7, #a29bfe)',
  ];

  // 控制动画的状态
  const showReveal = ref(false);
  let timer: ReturnType<typeof setTimeout> | null = null;

  // 监听 reveal prop 变化，延迟 0.8s 后启动动画
  watch(
    () => props.reveal,
    (newVal) => {
      // 清除之前的定时器（避免竞态）
      if (timer) clearTimeout(timer);

      if (newVal) {
        timer = setTimeout(() => {
          showReveal.value = true;
        }, 20);
      } else {
        // false → 立即重置为隐藏状态（无延迟）
        showReveal.value = false;
      }
    },
    { immediate: true } // 组件挂载时若 reveal 为 true 也会执行
  );

  // 组件卸载时清除定时器
  onBeforeUnmount(() => {
    if (timer) clearTimeout(timer);
  });
  </script>

  <style scoped>
  /* ---------- 容器 ---------- */
  .match-scores {
    position: relative;
    background: transparent;        /* 初始背景透明 */
    border-radius: 20px;
    padding: 12px 12px;
    width: 100%;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0); /* 阴影初始也透明，随后可一起显隐，按需调整 */
    overflow: hidden;              /* 保证背景填充不超出圆角 */
    transition: box-shadow 0.6s ease 0.8s; /* 阴影与动画同步出现（延迟同动画） */
  }

  .reveal-active {
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05); /* 动画完成后显示阴影 */
  }

  /* ---------- 从左向右填充的背景层 ---------- */
  .bg-fill {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: white;
    border-radius: 20px;
    transform: scaleX(0);          /* 初始无宽度（不可见） */
    transform-origin: left;        /* 以左边缘为基准展开 */
    transition: transform 0.6s ease;
    z-index: 0;
  }

  /* 激活时背景从左边开始向右拉伸至完整 */
  .reveal-active .bg-fill {
    transform: scaleX(1);
    transition-delay: 0.8s;        /* 延迟与 JS 定时器一致，形成整体 0.8s 后动画 */
  }

  /* ---------- 内容包裹层（用于淡入） ---------- */
  .content-wrapper {
    position: relative;
    z-index: 1;
    opacity: 0;                    /* 初始完全透明 */
    transition: opacity 0.6s ease;
  }

  .fade-in {
    opacity: 1;
    transition-delay: 0.8s;        /* 延迟 0.8s 后开始淡入 */
  }

  /* ---------- 其余样式保持不变（标题、柱状图等） ---------- */
  .match-scores h3 {
    font-size: 14px;
    margin-bottom: 12px;
    color: #333;
    font-weight: 600;
    text-align: center;
  }

  .bars-container {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 6px;
  }

  .bar-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    width: 28px;
  }

  .bar-wrapper {
    width: 7px;
    height: 50px;
    background: #f0f0f5;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    overflow: hidden;
  }

  .bar {
    width: 7px;
    border-radius: 8px 8px 0 0;
    transition: height 0.3s ease;
  }

  .score-value {
    font-size: 9px;
    font-weight: 600;
    color: #555;
  }

  .bar-label {
    font-size: 9px;
    color: #888;
    transform: rotate(-30deg);
    display: inline-block;
    white-space: nowrap;
    margin-top: 4px;
    transform-origin: center top;
  }
  </style>