<template>
  <view class="container">
    <!-- 上传区域 -->
    <view class="upload-section card">
      <view class="upload-title">上传新数据集</view>
      <view class="upload-placeholder" @click="selectFile">
        <image src="/static/zip-icon.png" class="upload-icon"></image>
        <text class="upload-text">点击选择 .zip 格式的数据集文件</text>
        <text class="upload-tip">文件结构需包含 /images 和 /labels 目录</text>
      </view>
      <view v-if="selectedFile" class="file-info">
        <text class="file-name">{{ selectedFile.name }}</text>
        <text class="file-size"
          >({{ (selectedFile.size / 1024).toFixed(1) }} KB)</text
        >
      </view>
      <button
        class="action-button"
        @click="uploadDataset"
        :disabled="!selectedFile || isUploading"
        :loading="isUploading"
      >
        {{ isUploading ? "上传中..." : "确认上传" }}
      </button>
    </view>

    <!-- 数据集列表 -->
    <view class="dataset-list card">
      <view class="list-title">可用数据集</view>
      <scroll-view
        class="list-scroll"
        scroll-y="true"
        @refresherrefresh="fetchDatasets"
        :refresher-enabled="true"
        :refresher-triggered="isRefreshing"
      >
        <view v-if="datasets.length > 0">
          <view
            v-for="(dataset, index) in datasets"
            :key="index"
            class="dataset-item"
          >
            <text class="dataset-name">{{ dataset }}</text>
            <text class="dataset-tag">已就绪</text>
          </view>
        </view>
        <view v-else class="no-data">
          <text>暂无可用数据集，请先上传</text>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
import { getAvailableDatasets, uploadDatasetZip } from "@/utils/api.js";

export default {
  data() {
    return {
      datasets: [],
      isRefreshing: false,
      selectedFile: null,
      isUploading: false,
    };
  },
  onLoad() {
    this.fetchDatasets();
  },
  methods: {
    async fetchDatasets() {
      this.isRefreshing = true;
      try {
        const token = uni.getStorageSync("token");
        this.datasets = await getAvailableDatasets(token);
        uni.showToast({ title: "列表已更新", icon: "none" });
      } catch (e) {
        uni.showToast({ title: "获取数据集列表失败", icon: "none" });
      } finally {
        this.isRefreshing = false;
      }
    },
    selectFile() {
      uni.chooseImage({
        count: 1,
        sourceType: ["album"], // 在H5端会打开文件选择器
        success: (res) => {
          const file = res.tempFiles[0];

          // 关键：在H5平台，即使用chooseImage，也可以选择任意文件，所以必须在这里校验文件类型
          if (!file.name.endsWith(".zip")) {
            uni.showToast({
              title: "格式错误，请选择.zip压缩包",
              icon: "none",
            });
            return;
          }
          this.selectedFile = file;
        },
        fail: (err) => {
          // 静默处理用户取消操作
          if (err.errMsg && err.errMsg.includes("cancel")) {
            return;
          }
          uni.showToast({ title: "选择文件失败", icon: "none" });
        },
      });
    },
    async uploadDataset() {
      if (!this.selectedFile) return;
      this.isUploading = true;
      try {
        const token = uni.getStorageSync("token");
        const res = await uploadDatasetZip(this.selectedFile.path, token);
        uni.showToast({ title: res.message || "上传成功" });
        this.selectedFile = null;
        this.fetchDatasets(); // 刷新列表
      } catch (err) {
        uni.showToast({ title: err.error || "上传失败", icon: "none" });
      } finally {
        this.isUploading = false;
      }
    },
  },
};
</script>

<style scoped>
.container {
  padding: 15px;
  background-color: #f7f8fa;
  min-height: 100vh;
}
.card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.upload-title,
.list-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f2f3f5;
  color: #303133;
}
.upload-placeholder {
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.3s;
}
.upload-placeholder:hover {
  background-color: #f2f3f5;
}
.upload-icon {
  width: 50px;
  height: 50px;
  margin-bottom: 15px;
  opacity: 0.8;
}
.upload-text {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
.file-info {
  margin-top: 15px;
  padding: 10px;
  background-color: #f2f3f5;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.file-name {
  font-size: 14px;
  color: #303133;
}
.file-size {
  font-size: 12px;
  color: #909399;
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
.dataset-list {
  flex: 1;
}
.list-scroll {
  height: 300px; /* 或者根据需要调整 */
}
.dataset-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 5px;
  border-bottom: 1px solid #f2f3f5;
}
.dataset-item:last-child {
  border-bottom: none;
}
.dataset-name {
  font-size: 16px;
  color: #303133;
}
.dataset-tag {
  background-color: #e8f5e9; /* Greenish background */
  color: #2e7d32; /* Dark green text */
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.no-data {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>
