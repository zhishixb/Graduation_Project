<template>
  <div class="spider-container">
    <div class="spider-top-container">
      <div class="job-spider-card">
        <JobSpiderByMajorCard></JobSpiderByMajorCard>
      </div>
      <div class="job-spider-card">
      </div>
      <div class="job-spider-card">
        <JobSpiderByPositionCard></JobSpiderByPositionCard>
      </div>
      <div class="job-spider-card"></div>
    </div>
    <div class="spider-bottom-container">
    </div>
  </div>
</template>

<script setup lang="ts">
import JobSpiderByMajorCard from "@/components/graduation_project/spider/top_card/JobSpiderByMajorCard.vue";
import JobSpiderByPositionCard from "@/components/graduation_project/spider/top_card/JobSpiderByPositionCard.vue";

</script>

<style scoped>

.spider-container{
  width: 980px;
  height: 560px;
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}

.spider-top-container{
  width: 100%;
  height: 170px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px
}

.spider-bottom-container{
  width: 100%;
  height: 370px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.job-spider-card{
  width: 230px;
  height: 150px;
  border-radius: 8px;
  display: flex;
  gap: 20px;
  background-color: #fefefe;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>