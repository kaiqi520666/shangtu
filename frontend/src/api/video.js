import request from "./request.js";

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

export function generateVideo({
  scenario = "product_video",
  type_id,
  title = null,
  input_mode,
  image_urls = [],
  input_video_url = null,
  user_prompt = null,
  duration,
  resolution,
  aspect_ratio,
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
      user_prompt,
      duration,
      resolution,
      aspect_ratio,
      settings_snapshot,
      sort_order,
      job_id,
    },
    { timeout: 60000 },
  );
}

export function optimizeFreeVideoPrompt(prompt) {
  return request.post("/video/free-video/optimize", { prompt }, { timeout: 120000 });
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
