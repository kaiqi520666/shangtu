import request from "./request.js";

export function getDigitalHumanAvatars(params = {}) {
  return request.get("/digital-human/avatars", { params, timeout: 15000 });
}

export function uploadPhotoAvatar({ file, name }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", name || "");
  return request.post("/digital-human/photo-avatars/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });
}

export function getPhotoAvatarTasks(params = {}) {
  return request.get("/digital-human/photo-avatars/tasks", { params, timeout: 15000 });
}

export function pollPhotoAvatarTask(taskId) {
  return request.get(`/digital-human/photo-avatars/tasks/${taskId}/poll`, { timeout: 15000 });
}

export function getPhotoAvatars(params = {}) {
  return request.get("/digital-human/photo-avatars", { params, timeout: 15000 });
}

export function deletePhotoAvatar(assetId) {
  return request.delete(`/digital-human/photo-avatars/${assetId}`, { timeout: 15000 });
}

export function getDigitalHumanVoices(params = {}) {
  return request.get("/digital-human/voices", { params, timeout: 15000 });
}

export function uploadDigitalHumanAudioAsset(file, { durationSeconds = 0 } = {}) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("duration_seconds", String(durationSeconds || 0));
  return request.post("/digital-human/audio-assets/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });
}

export function getDigitalHumanAudioAssets(params = {}) {
  return request.get("/digital-human/audio-assets", { params, timeout: 15000 });
}

export function deleteDigitalHumanAudioAsset(audioAssetId) {
  return request.delete(`/digital-human/audio-assets/${audioAssetId}`, { timeout: 15000 });
}

export function getDigitalHumanConfig() {
  return request.get("/digital-human/config", { timeout: 15000 });
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
