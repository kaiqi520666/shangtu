import request from "./request.js";

export function getDigitalHumanAvatars(params = {}) {
  return request.get("/digital-human/avatars", { params, timeout: 15000 });
}

export function getDigitalHumanVoices(params = {}) {
  return request.get("/digital-human/voices", { params, timeout: 15000 });
}

export function createDigitalHumanTask(payload) {
  return request.post("/digital-human/tasks", payload, { timeout: 30000 });
}

export function getDigitalHumanTask(taskId) {
  return request.get(`/digital-human/tasks/${taskId}`, { timeout: 15000 });
}

export function pollDigitalHumanTask(taskId) {
  return request.get(`/digital-human/tasks/${taskId}/poll`, { timeout: 15000 });
}

export function deleteDigitalHumanTask(taskId) {
  return request.delete(`/digital-human/tasks/${taskId}`, { timeout: 15000 });
}

export function getDigitalHumanDownloadUrl(taskId) {
  return `${request.defaults.baseURL}/digital-human/tasks/${taskId}/download`;
}
