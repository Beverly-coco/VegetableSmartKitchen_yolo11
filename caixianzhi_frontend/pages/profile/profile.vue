<template>
  <view class="container">
    <view class="profile-header">
      <image
        class="avatar"
        :src="userInfo.avatar"
        @click="openEditModal"
      ></image>
      <text class="username">{{ userInfo.username }}</text>
      <text class="user-id">ID: 10001</text>
    </view>

    <view class="menu-list">
      <view class="menu-item" @click="openEditModal">
        <text class="menu-text">编辑资料</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="navigateToDatasetManagement">
        <text class="menu-text">数据集管理</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="showAbout">
        <text class="menu-text">关于我们</text>
        <text class="arrow">›</text>
      </view>
    </view>

    <view class="logout-wrapper">
      <button class="logout-button" @click="handleLogout">退出登录</button>
    </view>

    <!-- 编辑资料弹窗 -->
    <view
      class="modal-mask"
      v-if="isEditModalVisible"
      @click.self="closeEditModal"
    >
      <view class="modal-content">
        <text class="modal-title">编辑资料</text>

        <view class="form-item avatar-item" @click="changeAvatar">
          <text class="form-label">头像</text>
          <view class="form-value">
            <image class="modal-avatar" :src="tempUserInfo.avatar"></image>
            <text class="arrow">›</text>
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">昵称</text>
          <input
            class="form-input"
            v-model="tempUserInfo.username"
            placeholder="输入新的昵称"
          />
        </view>

        <view class="form-item">
          <text class="form-label">性别</text>
          <view class="gender-selector">
            <text
              class="gender-option"
              :class="{ active: tempUserInfo.gender === '男' }"
              @click="tempUserInfo.gender = '男'"
              >男</text
            >
            <text
              class="gender-option"
              :class="{ active: tempUserInfo.gender === '女' }"
              @click="tempUserInfo.gender = '女'"
              >女</text
            >
            <text
              class="gender-option"
              :class="{ active: tempUserInfo.gender === '保密' }"
              @click="tempUserInfo.gender = '保密'"
              >保密</text
            >
          </view>
        </view>

        <view class="modal-actions">
          <button class="modal-button confirm" @click="saveUserInfo">
            保存
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getUserProfile, updateUserProfile, logout } from "@/utils/api.js";

// 导出默认的 Vue 组件
export default {
  // 定义组件的响应式数据
  data() {
    return {
      isEditModalVisible: false, // 控制编辑模态框是否可见
      userInfo: {
        username: "加载中...", // 用户名初始状态
        avatar: "/static/user-avatar.png", // 默认用户头像
        gender: "保密", // 默认性别
      },
      tempUserInfo: {}, // 临时用户信息对象，用于编辑时保存副本
    };
  },

  // 页面显示时触发（页面生命周期钩子）
  onShow() {
    this.fetchUserProfile(); // 显示页面时获取用户信息
  },

  // 定义方法
  methods: {
    // 获取用户信息方法
    async fetchUserProfile() {
      try {
        const res = await getUserProfile();
        this.userInfo.username = res.username;
        this.userInfo.gender = res.profile.gender;
        if (res.profile.avatar) {
          this.userInfo.avatar = `http://127.0.0.1:8000${res.profile.avatar}`;
        }
      } catch (error) {
        uni.showToast({ title: "获取用户信息失败", icon: "none" });
      }
    },

    // 打开编辑模态框
    async openEditModal() {
      this.tempUserInfo = JSON.parse(JSON.stringify(this.userInfo));
      try {
        const res = await getUserProfile();
        if (res.profile.avatar) {
          this.tempUserInfo.avatar = `http://127.0.0.1:8000${res.profile.avatar}`;
        }
      } catch (error) {
        // Silently fail, use cached avatar
      }
      this.isEditModalVisible = true;
    },

    // 关闭编辑模态框
    closeEditModal() {
      this.isEditModalVisible = false;
    },

    // 更换头像（相册/相机选择图片）
    changeAvatar() {
      uni.chooseImage({
        count: 1, // 选择一张图片
        sourceType: ["album", "camera"], // 来源为相册或相机
        success: (res) => {
          this.tempUserInfo.avatar = res.tempFilePaths[0]; // 用于页面预览
          this.tempUserInfo.newAvatarFile = res.tempFilePaths[0]; // 用于上传
        },
      });
    },

    // 保存用户信息到后端
    async saveUserInfo() {
      try {
        const formData = {
          username: this.tempUserInfo.username,
          gender: this.tempUserInfo.gender,
        };
        const res = await updateUserProfile(
          formData,
          this.tempUserInfo.newAvatarFile
        );

        this.userInfo.username = res.username;
        this.userInfo.gender = res.profile.gender;
        if (res.profile.avatar) {
          this.userInfo.avatar = `http://127.0.0.1:8000${res.profile.avatar}`;
        }
        this.closeEditModal();
        uni.showToast({ title: "保存成功" });
      } catch (error) {
        uni.showToast({
          title: `保存失败: ${error.detail || ""}`,
          icon: "none",
        });
      }
    },

    // 跳转到数据集管理页面
    navigateToDatasetManagement() {
      uni.navigateTo({
        url: "/pages/dataset/manage",
      });
    },

    // 显示"关于我们"对话框
    showAbout() {
      uni.showModal({
        title: "关于我们", // 弹窗标题
        content: "@两颗牙 蔬菜目标检测1.0", // 弹窗内容
        showCancel: false, // 不显示取消按钮
      });
    },

    // 注销登录，清除 token 并跳转登录页
    async handleLogout() {
      try {
        await logout();
        uni.removeStorageSync("token");
        uni.reLaunch({ url: "/pages/login/login" });
      } catch (error) {
        uni.showToast({ title: "登出失败", icon: "none" });
      }
    },
  },
};
</script>

<style scoped>
/* General */
.container {
  background-color: #f7f8fa;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
    Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
}

.arrow {
  color: #c8c8c8;
  font-size: 20px;
}

/* Header */
.profile-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 0;
  background: linear-gradient(to bottom, #6d40f6, #5a29e4);
  color: white;
}
.avatar {
  width: 85px;
  height: 85px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.username {
  margin-top: 15px;
  font-size: 20px;
  font-weight: 500;
}
.user-id {
  margin-top: 5px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

/* Menu */
.menu-list {
  margin: 20px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  transition: background-color 0.2s;
}
.menu-item:not(:last-child) {
  border-bottom: 1px solid #f5f5f5;
}
.menu-item:active {
  background-color: #fafafa;
}
.menu-text {
  font-size: 16px;
  color: #333;
}

/* Logout */
.logout-wrapper {
  margin: 30px 20px;
}
.logout-button {
  height: 48px;
  line-height: 48px;
  background-color: #fff;
  color: #ff4d4f;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}
.logout-button::after {
  border: none;
}

/* Modal */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: flex-end;
  z-index: 999;
}
.modal-content {
  width: 100%;
  background-color: #f7f8fa;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  padding: 20px;
  box-sizing: border-box;
}
.modal-title {
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 25px;
}

.form-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 10px;
  background-color: #fff;
  border-bottom: 1px solid #f5f5f5;
}
.form-item:first-of-type {
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}
.form-item:last-of-type {
  border-bottom: none;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}
.form-label {
  font-size: 16px;
  color: #333;
}
.form-value {
  display: flex;
  align-items: center;
  color: #999;
}
.modal-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  margin-right: 5px;
}
.form-input {
  text-align: right;
  font-size: 16px;
  color: #555;
}

.gender-selector {
  display: flex;
}
.gender-option {
  padding: 5px 12px;
  border: 1px solid #eee;
  border-radius: 15px;
  margin-left: 10px;
  font-size: 14px;
}
.gender-option.active {
  background-color: #5a29e4;
  color: #fff;
  border-color: #5a29e4;
}

.modal-actions {
  margin-top: 30px;
}
.modal-button.confirm {
  width: 100%;
  height: 48px;
  line-height: 48px;
  font-size: 16px;
  background-color: #5a29e4;
  color: #fff;
  border-radius: 24px;
}
</style>
