<!-- components/HotMajors.vue -->
<template>
  <div class="transactions">
    <h3>热门专业</h3>
    <div class="transaction-list">
      <div v-for="(t, i) in transactions" :key="i" class="t-item">
        <div class="t-icon"><span class="icon-dot"></span></div>
        <span class="t-name">{{ t.name }}</span>
        <span class="t-price">{{ t.price }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

// 内部静态数据，保持原样
const transactions = ref([
  { name: 'Starbucks', price: -21 },
  { name: 'Apple Store', price: -35 },
  { name: 'Verizon', price: -61 },
]);
</script>

<style scoped>
.transactions {
  width: 300px;
  background: white;
  border-radius: 24px;
  padding: 3px 24px;
  flex: 1;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
}

.transactions h3 {
  font-size: 18px;
  margin-bottom: 20px;
  color: #333;
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
  background: #F4F6FC;
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