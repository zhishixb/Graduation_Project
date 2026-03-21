<template>
  <div class="process-container">
    <div class="left-process-container">
    </div>
    <div class="right-process-container">
      <div class="top-right-process-container">
        <MajorJobProcessCard></MajorJobProcessCard>
        <MajorProcessCard></MajorProcessCard>
      </div>
      <div class="middle-right-process-container"></div>
      <div class="bottom-right-process-container"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MajorJobProcessCard from '@/components/graduation_project/process/right_card/top_right_card/MajorJobProcessCard.vue'
import MajorProcessCard from '@/components/graduation_project/process/right_card/top_right_card/MajorProcessCard.vue'

</script>

<style scoped>
.process-container{
  width: 980px;
  height: 520px;
  display: flex;
  flex-direction: row;
  gap: 20px;
}

.left-process-container{
  width: 620px;
  height: 520px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px
}

.right-process-container{
  width: 340px;
  height: 520px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.top-right-process-container{
  width: 100%;
  height: 150px;
  display: flex;
  flex-direction: row;
  gap: 20px;
}

.middle-right-process-container{
  width: 100%;
  height: 155px;
  gap: 20px;
}

.bottom-right-process-container{
  width: 100%;
  height: 155px;
}

</style>