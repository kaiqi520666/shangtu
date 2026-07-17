import request from "./request.js";
import { postSse } from "./sse.js";

function buildPublicApiUrl(path) {
  const baseURL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
  return `${baseURL}${path}`;
}

export function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/image/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });
}

export function analyzeImage(
  { images = [], platform = "", scenario = null, type_id = null },
  { signal, onChunk },
) {
  return postSse("/image/analyze", { images, platform, scenario, type_id }, { signal, onChunk });
}

export function generateImageStrategy({
  scenario,
  images = [],
  platform = "",
  language = "中文",
  product_input = "",
  module_ids = [],
  structure = [],
  scene_description = "",
  selected_model_name = "",
  scene_ids = [],
}) {
  return request.post(
    "/image/strategy",
    {
      scenario,
      images,
      platform,
      language,
      product_input,
      module_ids,
      structure,
      scene_description,
      selected_model_name,
      scene_ids,
    },
    { timeout: 120000 },
  );
}

export function optimizeFreeImagePrompt(prompt, { signal, onChunk }) {
  return postSse("/image/free-image/optimize", { prompt }, { signal, onChunk });
}

export function getImageCreditCosts() {
  return request.get("/image/credit-costs", { timeout: 15000 });
}

export function getImageCatalog() {
  return request.get("/image/catalog", { timeout: 15000 });
}

export async function getImageCapabilities() {
  const response = await fetch(buildPublicApiUrl("/image/capabilities"), {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`获取图片能力失败: ${response.status}`);
  }
  return response.json();
}

export function generateImage({
  user_prompt = null,
  image_urls = null,
  ratio,
  resolution,
  settings_snapshot = null,
  job_id = null,
  type_id = null,
  title = null,
  sort_order = 0,
}) {
  return request.post(
    "/image/generate",
    {
      user_prompt,
      image_urls,
      ratio,
      resolution,
      settings_snapshot,
      job_id,
      type_id,
      title,
      sort_order,
    },
    { timeout: 60000 },
  );
}

export function getImageTask(taskId) {
  return request.get(`/image/task/${taskId}`, { timeout: 15000 });
}

export function deleteImageTask(taskId) {
  return request.delete(`/image/task/${taskId}`, { timeout: 15000 });
}

export function getImageDownloadUrl(taskId) {
  // 返回后端代理下载的完整 URL（带 token 的请求需要用 fetch）
  return `${request.defaults.baseURL}/image/task/${taskId}/download`;
}

export function regenerateImageTask(taskId, editInstruction, userPrompt = null) {
  return request.post(
    `/image/task/${taskId}/regenerate`,
    { edit_instruction: editInstruction, user_prompt: userPrompt },
    { timeout: 60000 },
  );
}
