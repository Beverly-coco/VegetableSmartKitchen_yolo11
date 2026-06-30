<template>
  <view class="container">
    <!-- 上传区域 -->
    <view class="upload-section">
      <image
        class="preview-image"
        v-if="previewImageSrc"
        :src="previewImageSrc"
        mode="aspectFit"
      ></image>
      <view v-else class="placeholder" @click="chooseImage">
        <image
          class="placeholder-icon"
          src="/static/image-icon.png"
          mode="aspectFit"
        ></image>
        <text class="placeholder-text">点击上传蔬菜图片</text>
      </view>
      <button
        class="upload-button"
        @click="uploadImage"
        :disabled="!previewImageSrc || isLoading"
      >
        <text v-if="!isLoading">开始识别</text>
        <view v-else class="loading-spinner"></view>
      </button>
    </view>

    <!-- 结果展示区域 -->
    <scroll-view
      class="results-section"
      scroll-y="true"
      v-if="detectionResults.imageUrl"
    >
      <view class="result-image-wrapper">
        <image
          class="result-image"
          :src="detectionResults.imageUrl"
          mode="widthFix"
        ></image>
      </view>
      <view class="result-title">识别结果</view>
      <view
        v-for="(item, index) in detectionResults.detections"
        :key="index"
        class="result-card"
      >
        <view class="card-header">
          <text class="vegetable-name">{{
            getDisplayName(item.chinese_name, item.class_name)
          }}</text>
          <text class="confidence"
            >置信度: {{ (item.confidence * 100).toFixed(1) }}%</text
          >
        </view>
        <view class="knowledge-section">
          <view class="knowledge-title">小知识</view>
          <text class="knowledge-desc">{{ item.knowledge.description }}</text>
          <view class="nutrition-grid">
            <view
              class="nutrition-item"
              v-for="(value, key) in item.knowledge.nutrition"
              :key="key"
            >
              <text class="nutrition-key">{{ key }}</text>
              <text class="nutrition-value">{{ value }}</text>
            </view>
          </view>
        </view>
      </view>
      <view
        v-if="detectionResults.detections.length === 0"
        class="no-detection"
      >
        <text>未能识别出任何蔬菜，换张图片试试吧！</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { uploadSingleImage } from "@/utils/api.js";

export default {
  // 组件的响应式数据
  data() {
    return {
      previewImageSrc: null, // 本地预览图地址
      tempFile: null, // 暂存的图片文件
      isLoading: false,
      detectionResults: {
        // 识别返回的完整结果
        imageUrl: "",
        detections: [],
      },
    };
  },
  // 定义所有方法
  methods: {
    // 选择图片
    chooseImage() {
      uni.chooseImage({
        count: 1, // 只选择一张图片
        sourceType: ["album", "camera"], // 从相册和相机选择
        success: (res) => {
          this.previewImageSrc = res.tempFilePaths[0];
          this.detectionResults = {}; // 清空上次结果
        },
      });
    },
    // 格式化显示的蔬菜名称
    getDisplayName(chineseName, englishName) {
      if (chineseName && chineseName !== englishName) {
        return `${chineseName} (${englishName})`;
      }
      return englishName;
    },
    // 上传图片至后端进行识别
    async uploadImage() {
      if (!this.previewImageSrc) {
        uni.showToast({ title: "请先选择图片", icon: "none" });
        return;
      }
      this.isLoading = true;
      try {
        const res = await uploadSingleImage(this.previewImageSrc);
        this.detectionResults = res;
      } catch (err) {
        uni.showToast({
          title: `识别失败: ${err.error || "请检查网络"}`,
          icon: "none",
        });
      } finally {
        this.isLoading = false;
      }
    },
  },
};
</script>

<style>
/* 使页面占满可用高度，并禁止页面本身滚动 */
page {
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100%; /* 从 100vh 改为 100%，以继承 page 的正确高度 */
  background-color: #f7f8fa;
}

/* 上传区域样式 */
.upload-section {
  padding: 20px;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.preview-image {
  max-width: 100%;
  max-height: 200px; /* 限制预览图最大高度 */
  border-radius: 12px;
  margin-bottom: 20px;
}

.placeholder {
  width: 100%;
  height: 150px;
  background-color: #f7f8fa;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.3s;
}

.placeholder:hover {
  background-color: #f2f3f5;
}

.placeholder-icon {
  width: 40px;
  height: 40px;
  opacity: 0.5;
}

.placeholder-text {
  margin-top: 10px;
  font-size: 16px;
  color: #999;
}

.upload-button {
  width: 80%;
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

.upload-button:disabled {
  background: #c8c9cc;
  box-shadow: none;
  color: #ffffff;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto; /* 居中 */
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 结果展示区域 */
.results-section {
  flex: 1;
  padding: 15px;
  box-sizing: border-box;
  min-height: 0;
}
.result-image-wrapper {
  margin-bottom: 20px;
}
.result-image {
  width: 100%;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
.result-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #303133;
}
.result-card {
  background-color: #ffffff;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 15px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid #f2f3f5;
  margin-bottom: 10px;
}
.vegetable-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.confidence {
  font-size: 14px;
  color: #606266;
  background-color: #f0f2f5;
  padding: 3px 8px;
  border-radius: 10px;
}
.knowledge-section {
  margin-top: 10px;
}
.knowledge-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}
.knowledge-desc {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}
.nutrition-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 20px; /* 垂直间距10px，水平间距20px */
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f2f3f5;
}
.nutrition-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px; /* 增加内边距 */
  background-color: #f7f8fa;
  border-radius: 8px; /* 增加圆角 */
  font-size: 13px; /* 调整字体大小 */
}
.nutrition-key {
  font-weight: 500;
  color: #606266;
}
.nutrition-value {
  color: #303133;
  font-weight: 500; /* 让数值也加粗一些 */
}
.no-detection {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}
</style>
