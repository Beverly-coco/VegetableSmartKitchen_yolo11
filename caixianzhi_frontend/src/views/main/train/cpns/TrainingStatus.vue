<template>
  <!-- No changes to template section -->
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { getTrainingResult } from "../../services/trainingService";

const props = defineProps({
  taskId: {
    type: String,
    required: true,
  },
});

const taskStatus = ref("");
const visualizationUrl = ref("");
const showResultButton = ref(false);
const pollingTimer = ref(null);

// 获取训练日志和状态
const pollTrainingStatus = async () => {
  if (!props.taskId) return;

  try {
    const response = await getTrainingResult(props.taskId); // 改为调用新的 getTrainingResult
    taskStatus.value = response.status;

    // 如果训练完成，则停止轮询并显示结果
    if (response.status === "completed") {
      if (pollingTimer.value) clearInterval(pollingTimer.value);
      visualizationUrl.value = response.visualization_url; // 获取最终的可视化图片URL
      showResultButton.value = true; // 显示查看结果按钮
    } else if (response.status === "failed") {
      if (pollingTimer.value) clearInterval(pollingTimer.value);
      // 可以选择在这里处理失败状态，例如显示错误信息
      console.error("训练任务失败:", response.error);
    }
  } catch (error) {
    console.error("轮询训练状态失败:", error);
    if (pollingTimer.value) clearInterval(pollingTimer.value);
  }
};

// 启动轮询
onMounted(() => {
  pollingTimer.value = setInterval(pollTrainingStatus, 5000); // 5秒轮询一次
});

onBeforeUnmount(() => {
  if (pollingTimer.value) clearInterval(pollingTimer.value);
});
</script>

<style>
/* No changes to style section */
</style>
