import http from "./http";

// 获取训练服务相关的数据

// 启动训练任务
export function startTraining(params) {
  return http.post("/train/", params);
}

// 获取可用的数据集列表
export function getAvailableDatasets() {
  return http.get("/datasets/");
}

// 获取可用的基础模型列表
export function getAvailableModels() {
  return http.get("/train/available-models/");
}

// 获取训练结果
export function getTrainingResult(taskId) {
  return http.get(`/train/result/${taskId}/`);
}
