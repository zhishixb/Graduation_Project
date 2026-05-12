<template>
  <div class="info-content">
    <h1>{{ jobData.function_name }}</h1>

    <div class="scroll-content">
      <h3>岗位技能</h3>
      <p class="skill-note">
        注：技能词源自招聘文本，单个岗位的技能需求不包含全部内容。由于岗位信息仅按照岗位名称获取，可能存在一定的杂糅（例如客服经理，信息来源可能是多个行业的客服经理，技能词可能涉及多个行业领域）。
      </p>

      <!-- 技能标签 -->
      <div v-if="skillList.length > 0" class="tag-list">
        <span v-for="(skill, index) in skillList" :key="index" class="tag">
          {{ skill }}
        </span>
      </div>
      <div v-else class="text-muted">暂无技能数据</div>

      <h3>涉及领域</h3>
      <!-- 领域标签 -->
      <div v-if="categoryList.length > 0" class="tag-list">
        <span v-for="(cat, index) in categoryList" :key="index" class="tag">
          {{ cat }}
        </span>
      </div>
      <div v-else class="text-muted">暂无领域数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  jobData: {
    type: Object,
    required: true
  }
});

// 处理技能数组/字符串
const skillList = computed(() => {
  const raw = props.jobData.skills;
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'string') {
    return raw.split(/[，,]/).map(s => s.trim()).filter(s => s.length > 0);
  }
  return [];
});

// 处理领域数组/字符串
const categoryList = computed(() => {
  const raw = props.jobData.category;
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'string') {
    return raw.split(/[，,]/).map(s => s.trim()).filter(s => s.length > 0);
  }
  return [];
});
</script>

<style scoped>
.info-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 28px 24px 0 24px;
  color: #2c3e50;
  box-sizing: border-box;
}

h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: #1a1a2e;
  line-height: 1.4;
  flex-shrink: 0;
}

.scroll-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 28px;
  padding-right: 4px;
  box-sizing: border-box;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scroll-content::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 8px 0;
  color: #3a4a5c;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  padding-bottom: 4px;
}

.text-block {
  font-size: 14px;
  line-height: 1.8;
  color: #4b5563;
  margin-bottom: 8px;
}

.text-muted {
  font-size: 14px;
  color: #aaa;
  font-style: italic;
}

/* 提示文字 */
.skill-note {
  font-size: 12px;
  color: #999;
  line-height: 1.6;
  margin: 0 0 16px 0;
}

/* 标签容器（技能 & 领域共用） */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

/* 统一轻量标签样式 */
.tag {
  display: inline-block;
  padding: 2px 10px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  border-radius: 10px;
  line-height: 1.6;
  white-space: nowrap;
}
</style>