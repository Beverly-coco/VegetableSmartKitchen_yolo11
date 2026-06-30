<template>
  <view class="container">
    <view class="header">
      <text class="title">您好,</text>
      <text class="subtitle">欢迎使用蔬菜识别系统</text>
    </view>
    <view class="form-wrapper">
      <form @submit="handleLogin" class="form-container">
        <view class="input-wrapper">
          <input
            class="input-field"
            placeholder="用户名 (user)"
            v-model="username"
          />
        </view>
        <view class="input-wrapper">
          <input
            class="input-field"
            type="password"
            placeholder="密码 (user123)"
            v-model="password"
          />
        </view>
        <button class="login-button" form-type="submit">登 录</button>
      </form>
    </view>
  </view>
</template>

<script>
import { login } from "@/utils/api.js"; // 导入封装好的 login 函数

// 默认导出一个 Vue 组件对象
export default {
  // 定义组件的响应式数据
  data() {
    return {
      username: "", // 用户输入的用户名
      password: "", // 用户输入的密码
    };
  },
  // 定义组件的方法
  methods: {
    // 登录处理函数
    async handleLogin() {
      // 检查用户名或密码是否为空
      if (!this.username || !this.password) {
        // 弹出提示框，提醒用户填写完整
        uni.showToast({
          title: "请输入用户名和密码", // 提示文字
          icon: "none", // 不显示图标
        });
        return; // 阻止后续执行
      }

      try {
        const res = await login({
          username: this.username, // 请求体中包含用户名
          password: this.password, // 请求体中包含密码
        });

        if (res.token) {
          // 将 token 缓存到本地，供后续接口使用
          uni.setStorageSync("token", res.token);
          // 重新启动应用并跳转到首页
          uni.reLaunch({
            url: "/pages/index/index", // 首页路径
          });
        } else {
          // 登录失败，弹出错误信息
          uni.showToast({
            title: "用户名或密码错误",
            icon: "none",
          });
        }
      } catch (err) {
        // 检查后端是否返回了具体的错误信息
        if (err.statusCode === 400 || err.statusCode === 401) {
          uni.showToast({
            title: "用户名或密码错误", // 更精确的提示
            icon: "none",
          });
        } else {
          // 其他网络层面的错误
          uni.showToast({
            title: "网络请求失败，请检查服务",
            icon: "none",
          });
        }
      }
    },
  },
};
</script>

<style scoped>
.container {
  height: 100vh;
  background: linear-gradient(to bottom, #6d40f6, #5a29e4);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 50px 30px;
  box-sizing: border-box;
}
.header {
  padding-top: 30px;
}
.title {
  font-size: 32px;
  color: #fff;
  font-weight: bold;
}
.subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 10px;
  display: block;
}
.form-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.form-container {
  background-color: #fff;
  border-radius: 16px;
  padding: 30px 25px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}
.input-wrapper {
  border-bottom: 1px solid #f0f0f0;
  padding: 5px 0;
  margin-bottom: 20px;
}
.input-field {
  height: 50px;
  font-size: 16px;
  color: #333;
}
.input-field::placeholder {
  /* Chrome, Firefox, Opera, Safari 10.1+ */
  color: #bbb;
  opacity: 1;
  /* Firefox */
}
.login-button {
  height: 50px;
  line-height: 50px;
  background: linear-gradient(to right, #6d40f6, #5a29e4);
  color: #fff;
  border-radius: 25px;
  font-size: 18px;
  font-weight: bold;
  margin-top: 20px;
  box-shadow: 0 8px 20px rgba(90, 41, 228, 0.3);
}
.login-button::after {
  border: none;
}
</style>
