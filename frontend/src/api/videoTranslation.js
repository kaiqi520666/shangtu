import request from "./request.js";

export function getVideoTranslationConfig() {
  return request.get("/video-translation/config", { timeout: 15000 });
}

export function getVideoTranslationLanguages() {
  return request.get("/video-translation/languages", { timeout: 15000 });
}

export function createVideoTranslationTask(payload) {
  return request.post("/video-translation/tasks", payload, { timeout: 60000 });
}

export function getVideoTranslationTask(taskId) {
  return request.get(`/video-translation/tasks/${taskId}`, { timeout: 15000 });
}

export function pollVideoTranslationTask(taskId) {
  return request.get(`/video-translation/tasks/${taskId}/poll`, { timeout: 15000 });
}

export function deleteVideoTranslationTask(taskId) {
  return request.delete(`/video-translation/tasks/${taskId}`, { timeout: 15000 });
}

export function getVideoTranslationDownloadUrl(taskId) {
  return `${request.defaults.baseURL}/video-translation/tasks/${taskId}/download`;
}
