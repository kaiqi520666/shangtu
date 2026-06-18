import request from "./request.js";

export function getVideoCreditCosts() {
  return request.get("/video/credit-costs", { timeout: 15000 });
}

export function generateVideo({
  type_id,
  title = null,
  input_mode,
  image_urls = [],
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
      type_id,
      title,
      input_mode,
      image_urls,
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

export function getVideoTask(taskId) {
  return request.get(`/video/task/${taskId}`, { timeout: 15000 });
}

export function deleteVideoTask(taskId) {
  return request.delete(`/video/task/${taskId}`, { timeout: 15000 });
}

export function getVideoDownloadUrl(taskId) {
  return `${request.defaults.baseURL}/video/task/${taskId}/download`;
}
