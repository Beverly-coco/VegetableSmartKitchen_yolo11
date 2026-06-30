const BASE_URL = "http://127.0.0.1:8000/api"; // 您的后端地址

/**
 * 封装 uni.request
 * @param {object} options - uni.request 的参数
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync("token");

    // 默认请求头
    const header = {
      ...options.header,
    };

    // 如果 token 存在，则添加到请求头
    if (token) {
      header["Authorization"] = `Token ${token}`;
    }

    uni.request({
      ...options,
      url: `${BASE_URL}${options.url}`,
      header,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          // Token 失效或未授权，跳转到登录页
          uni.showToast({ title: "请先登录", icon: "none" });
          uni.reLaunch({ url: "/pages/login/login" });
          reject(res.data);
        } else {
          // 其他错误
          reject(res.data);
        }
      },
      fail: (err) => {
        uni.showToast({ title: "网络请求失败", icon: "none" });
        reject(err);
      },
    });
  });
}

// 封装 GET, POST, UPLOAD 等方法
const http = {
  get: (url, data) => request({ url, method: "GET", data }),
  post: (url, data) => request({ url, method: "POST", data }),
  upload: (url, filePath, formData = {}, name = "image") => {
    return new Promise((resolve, reject) => {
      const token = uni.getStorageSync("token");
      uni.uploadFile({
        url: `${BASE_URL}${url}`,
        filePath,
        name: name,
        formData,
        header: {
          Authorization: `Token ${token}`,
        },
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(JSON.parse(res.data));
          } else {
            reject(JSON.parse(res.data));
          }
        },
        fail: (err) => {
          reject(err);
        },
      });
    });
  },
};

export default http;

// 具体的 API 调用函数

// --- 认证 ---
export const login = (credentials) => http.post("/login/", credentials);
export const logout = () => http.post("/logout/");

// --- 识别 ---
export const uploadSingleImage = (filePath) => {
  return http.upload("/upload-single/", filePath);
};

// --- 数据集 ---
export const getAvailableDatasets = () => http.get("/datasets/");

export const uploadDatasetZip = (filePath) => {
  return http.upload("/upload-dataset/", filePath, {}, "dataset");
};

// --- 训练 ---
export const getAvailableModels = () => http.get("/train/available-models/");
export const startTrainingTask = (params) => http.post("/train/", params);
export const getTrainingLogs = (taskId) => http.get(`/train/result/${taskId}/`); // 指向新的 result API

// --- 用户 ---
export const getUserProfile = () => http.get("/profile/");

export const updateUserProfile = (formData, filePath) => {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync("token");
    uni.uploadFile({
      url: `${BASE_URL}/profile/`,
      filePath: filePath || "",
      name: "avatar",
      formData,
      header: {
        Authorization: `Token ${token}`,
      },
      method: "POST",
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(res.data));
        } else {
          reject(JSON.parse(res.data));
        }
      },
      fail: (err) => {
        reject(err);
      },
    });
  });
};
