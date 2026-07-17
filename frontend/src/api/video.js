import request from "./request.js";
import { postSse } from "./sse.js";

export function getVideoCreditCosts() {
  return request.get("/video/credit-costs", { timeout: 15000 });
}

export function generateVideoStrategy(payload) {
  return request.post("/video/strategy", payload, { timeout: 120000 });
}

export function uploadVideo(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/video/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000,
  });
}

export function uploadAudio(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/video/audio-upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000,
  });
}

export function generateVideo({
  scenario = "product_video",
  type_id,
  title = null,
  input_mode,
  image_urls = [],
  input_video_url = null,
  video_urls = [],
  audio_urls = [],
  user_prompt = null,
  duration,
  resolution,
  aspect_ratio,
  generate_audio = false,
  enable_web_search = false,
  settings_snapshot = null,
  sort_order = 0,
  job_id = null,
}) {
  return request.post(
    "/video/generate",
    {
      scenario,
      type_id,
      title,
      input_mode,
      image_urls,
      input_video_url,
      video_urls,
      audio_urls,
      user_prompt,
      duration,
      resolution,
      aspect_ratio,
      generate_audio,
      enable_web_search,
      settings_snapshot,
      sort_order,
      job_id,
    },
    { timeout: 60000 },
  );
}

export function optimizeFreeVideoPrompt(prompt, { signal, onChunk }) {
  return postSse("/video/free-video/optimize", { prompt }, { signal, onChunk });
}

export function getVideoTask(taskId) {
  return request.get(`/video/task/${taskId}`, { timeout: 15000 });
}

export function deleteVideoTask(taskId) {
  return request.delete(`/video/task/${taskId}`, { timeout: 15000 });
}

export function getVideoDownloadUrl(taskId) {
  return `${request.defaults.baseURL}/video/task/${taskId}/download`;
}
