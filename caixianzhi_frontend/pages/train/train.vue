<template>
  <view class="container">
    <!-- 参数配置 -->
    <view class="card">
      <view class="card-title">训练参数配置</view>

      <view class="form-item">
        <text class="form-label">选择数据集:</text>
        <picker
          @change="bindPickerChange($event, 'datasetIndex')"
          :value="datasetIndex"
          :range="availableDatasets"
          class="picker-wrapper"
        >
          <view class="picker">
            {{ availableDatasets[datasetIndex] || "请选择" }}
            <text class="arrow"></text>
          </view>
        </picker>
      </view>

      <view class="form-item">
        <text class="form-label">选择基础模型:</text>
        <picker
          @change="bindPickerChange($event, 'modelIndex')"
          :value="modelIndex"
          :range="availableModels"
          class="picker-wrapper"
        >
          <view class="picker">
            {{ availableModels[modelIndex] || "请选择" }}
            <text class="arrow"></text>
          </view>
        </picker>
      </view>

      <view class="form-item">
        <text class="form-label">训练轮数 (Epochs):</text>
        <input
          class="form-input"
          type="number"
          v-model.number="params.epochs"
        />
      </view>

      <view class="form-item">
        <text class="form-label">批次大小 (Batch):</text>
        <input
          class="form-input"
          type="number"
          v-model.number="params.batch_size"
        />
      </view>

      <button
        class="action-button"
        @click="startTraining"
        :disabled="
          isTraining || isLoadingInitialData || !availableDatasets.length
        "
        :loading="isTraining"
      >
        {{ isTraining ? "正在训练..." : "开始训练" }}
      </button>

      <view v-if="initialDataFailed" class="retry-container">
        <button class="retry-button" @click="fetchInitialData">
          获取初始数据失败，点击重试
        </button>
      </view>
    </view>

    <!-- 训练状态 -->
    <view class="card" v-if="task.id">
      <view class="card-title">训练状态</view>
      <view class="status-line">
        <text class="status-label">任务ID:</text>
        <text class="task-id">{{ task.id }}</text>
      </view>
      <view class="status-line">
        <text class="status-label">状态:</text>
        <text :class="['status-text', 'status-' + task.status]">{{
          task.status_text
        }}</text>
      </view>
    </view>

    <!-- 训练可视化图表 (已禁用) -->
    <!--
    <view class="card" v-if="hasChartData">
      <view class="card-title">训练可视化</view>
      <view class="chart-wrapper">
        <mrsongCharts
          type="line"
          title="损失函数曲线"
          :chartsData="lossChartData"
          :options="chartOptions"
        />
      </view>
      <view class="chart-wrapper">
        <mrsongCharts
          type="line"
          title="模型mAP曲线"
          :chartsData="mapChartData"
          :options="chartOptions"
        />
      </view>
    </view>
    -->

    <!-- 结果展示 -->
    <view class="card" v-if="task.status === 'completed'">
      <view class="card-title">训练结果图表</view>
      <view class="result-images">
        <view
          v-for="(img, index) in task.result_images"
          :key="index"
          class="result-image-item"
        >
          <image
            :src="img.url"
            mode="widthFix"
            class="result-image"
            @click="previewImage(img.url)"
          ></image>
          <text class="image-name">{{ img.name }}</text>
        </view>
      </view>
      <view v-if="!task.result_images.length" class="no-result">
        <text>训练完成，但未生成任何结果图表。</text>
      </view>
    </view>
  </view>
</template>

<script>
import {
  getAvailableDatasets,
  getAvailableModels,
  startTrainingTask,
  getTrainingLogs,
} from "@/utils/api.js";
// import mrsongCharts from "../../uni_modules/mrsong-charts/components/mrsong-charts/mrsong-charts.vue";

export default {
  // components: {
  //   mrsongCharts,
  // },
  data() {
    return {
      availableDatasets: [],
      datasetIndex: 0,
      availableModels: [],
      modelIndex: 0,
      params: {
        epochs: 10,
        batch_size: 2,
      },
      isTraining: false,
      task: {
        id: null,
        status: "",
        status_text: "",
        result_images: [],
        timer: null,
      },
      isLoadingInitialData: false,
      initialDataFailed: false,
    };
  },
  onShow() {
    this.fetchInitialData();
  },
  onUnload() {
    if (this.task.timer) {
      clearInterval(this.task.timer);
    }
  },
  methods: {
    async fetchInitialData() {
      this.isLoadingInitialData = true;
      this.initialDataFailed = false;
      try {
        this.availableDatasets = await getAvailableDatasets();
        this.availableModels = await getAvailableModels();
      } catch (e) {
        uni.showToast({ title: "获取初始数据失败", icon: "none" });
        this.initialDataFailed = true;
      } finally {
        this.isLoadingInitialData = false;
      }
    },
    bindPickerChange(e, type) {
      this[type] = e.detail.value;
    },
    resetTask() {
      if (this.task.timer) clearInterval(this.task.timer);
      this.task = {
        id: null,
        status: "",
        status_text: "",
        result_images: [],
        timer: null,
      };
    },
    async startTraining() {
      this.isTraining = true;
      this.resetTask();

      this.$nextTick(async () => {
        try {
          const trainingData = {
            dataset_name: this.availableDatasets[this.datasetIndex],
            base_model: this.availableModels[this.modelIndex],
            ...this.params,
          };

          const res = await startTrainingTask(trainingData);

          this.task.id = res.task_id;
          this.task.status = "starting";
          this.task.status_text = "任务已启动，请稍后...";
          this.startPolling();
        } catch (err) {
          uni.showToast({
            title: `启动失败: ${err.error || "未知错误"}`,
            icon: "none",
          });
          this.task.status = "failed";
          this.task.status_text = "启动失败";
          this.isTraining = false;
        }
      });
    },
    startPolling() {
      this.task.timer = setInterval(async () => {
        try {
          const res = await getTrainingLogs(this.task.id);
          this.updateTaskStatus(res);
        } catch (error) {
          console.error("轮询失败:", error);
          this.task.status = "failed";
          this.task.status_text = "轮询失败";
          this.isTraining = false;
          if (this.task.timer) clearInterval(this.task.timer);
        }
      }, 5000); // 5秒轮询一次
    },
    updateTaskStatus(res) {
      const statusMap = {
        starting: "启动中",
        running: "正在运行",
        completed: "已完成",
        failed: "失败",
      };
      this.task.status = res.status;
      this.task.status_text = statusMap[res.status] || "未知状态";

      if (res.status === "completed" || res.status === "failed") {
        this.isTraining = false;
        if (this.task.timer) clearInterval(this.task.timer);

        if (res.status === "completed" && res.visualization_url) {
          this.task.result_images = [
            { name: "results.png", url: res.visualization_url },
          ];
        }
      }
    },
    previewImage(url) {
      uni.previewImage({
        urls: [url],
      });
    },
  },
};
</script>

<style>
page {
  background-color: #f7f8fa;
}
.container {
  padding: 15px;
}
.card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f2f3f5;
  color: #303133;
}
.form-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f2f3f5;
}
.form-item:last-of-type {
  border-bottom: none;
}
.form-label {
  font-size: 15px;
  color: #606266;
}
.picker-wrapper {
  flex: 1;
}
.picker {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  font-size: 15px;
  color: #303133;
}
.arrow {
  width: 8px;
  height: 8px;
  border-top: 2px solid #999;
  border-right: 2px solid #999;
  transform: rotate(45deg);
  margin-left: 8px;
}
.form-input {
  font-size: 15px;
  color: #303133;
  text-align: right;
  border: none;
  background-color: transparent;
}
.action-button {
  width: 100%;
  margin-top: 20px;
  padding: 12px 0;
  background: linear-gradient(to right, #6d40f6, #5a29e4);
  color: white;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 500;
  border: none;
  box-shadow: 0 4px 12px rgba(96, 61, 236, 0.3);
  transition: all 0.3s;
}
.action-button[disabled] {
  background: #c8c9cc;
  box-shadow: none;
  color: #ffffff;
}
.retry-container {
  text-align: center;
  margin-top: 15px;
}
.retry-button {
  display: inline-block;
  padding: 8px 15px;
  background-color: #f2f3f5;
  color: #606266;
  border: 1px solid #dcdfe6;
  border-radius: 20px;
  font-size: 14px;
}
.status-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
}
.status-label {
  color: #606266;
}
.task-id {
  font-family: monospace;
  font-size: 12px;
  background-color: #f2f3f5;
  padding: 2px 6px;
  border-radius: 4px;
}
.status-text {
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 12px;
  color: white;
}
.status-starting,
.status-running {
  background-color: #3498db;
}
.status-completed {
  background-color: #2ecc71;
}
.status-failed {
  background-color: #e74c3c;
}
.chart-wrapper {
  margin-top: 15px;
  width: 100%;
  height: 220px;
}
.logs-container {
  margin-top: 15px;
}
.logs-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
  display: block;
}
.result-images {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}
.result-image-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.result-image {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}
.image-name {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}
.no-result {
  text-align: center;
  padding: 20px;
  color: #909399;
}
</style>
