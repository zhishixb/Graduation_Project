<template>
  <div class="hot-majors" @click="handleClick">
    <div class="content-wrapper" :class="{ 'fade-in': showReveal }">
      <h1 class="list-title">
        <n-icon size="18" class="title-icon">
          <ThermometerOutline />
        </n-icon>
        热门专业
      </h1>
      <div class="major-list">
        <div v-for="(major, idx) in displayMajors" :key="idx" class="major-item">
          <span class="rank">{{ idx + 1 }}</span>
          <span class="major-name">{{ major.name }}</span>
          <span class="heat-score">{{ major.heatDisplay }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { ThermometerOutline } from '@vicons/ionicons5';
import { useDataStore } from '@/stores/achieve/dataStore.ts';
import { getHotMajors } from '@/apis/business.ts';

const store = useDataStore();

export interface MajorHeatItem {
  name: string;
  heat_value: number;
}

const props = withDefaults(defineProps<{
  reveal?: boolean;
}>(), {
  reveal: false,
});

const showReveal = ref(false);
let timer: ReturnType<typeof setTimeout> | null = null;

// 存储原始数据
const rawMajors = ref<MajorHeatItem[]>([]);

// 取前8条并格式化热度值
const displayMajors = computed(() =>
  rawMajors.value.slice(0, 8).map(item => {
    const val = item.heat_value;
    let display: string;
    if (val >= 10000) {
      display = (val / 10000).toFixed(1).replace(/\.0$/, '') + '万';
    } else {
      display = val.toLocaleString();
    }
    return { ...item, heatDisplay: display };
  })
);

const handleClick = () => {
  store.isLoading = true;
  setTimeout(() => {
    store.turnToPage('hotMajor');
  }, 400);
};

// 获取后端数据
const fetchData = async () => {
  try {
    const res = await getHotMajors(30);
    if (res.success && Array.isArray(res.data?.majors)) {
      rawMajors.value = res.data.majors;
    }
  } catch (e) {
    console.error('获取热门专业失败', e);
  }
};

watch(
  () => props.reveal,
  (newVal) => {
    if (timer) clearTimeout(timer);
    if (newVal) {
      timer = setTimeout(() => {
        showReveal.value = true;
      }, 20);
    } else {
      showReveal.value = false;
    }
  },
  { immediate: true }
);

onMounted(() => {
  fetchData();
});

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer);
});
</script>

<style scoped>
.hot-majors {
  position: relative;
  background: transparent;
  border-radius: 20px;
  padding: 12px;
  width: 90%;
  box-sizing: border-box;
  overflow: hidden;
  cursor: pointer;
  transition: background 0.2s;
}
.hot-majors:hover {
  background: rgba(0, 0, 0, 0.03);
}

.content-wrapper {
  position: relative;
  z-index: 1;
  opacity: 0;
  transition: opacity 0.6s ease;
}

.fade-in {
  opacity: 1;
  transition-delay: 0.8s;
}

.list-title {
  font-size: 18px;
  margin-bottom: 12px;
  color: #333;
  font-weight: 600;
  text-align: left;
  display: flex;
  align-items: center;
}

.title-icon {
  margin-right: 6px;
}

.major-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.major-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #444;
}

.rank {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f5;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  color: #6C5CE7;
  flex-shrink: 0;
}

.major-name {
  flex: 1;
  font-weight: 500;
}

.heat-score {
  font-weight: 600;
  color: #6C5CE7;
  min-width: 40px;
  text-align: right;
}
</style>