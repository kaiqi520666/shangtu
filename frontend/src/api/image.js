import request from "./request.js";

export function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/image/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });
}

export function analyzeImage({ images = [], platform = "", scenario = null, type_id = null }) {
  return request.post("/image/analyze", { images, platform, scenario, type_id }, { timeout: 120000 });
}

export function generateProductImageStrategy({
  images = [],
  platform = "",
  language = "中文",
  product_input,
  module_ids,
}) {
  return request.post(
    "/image/product-image/strategy",
    { images, platform, language, product_input, module_ids },
    { timeout: 120000 },
  );
}

export function optimizeFreeImagePrompt(prompt) {
  return request.post("/image/free-image/optimize", { prompt }, { timeout: 120000 });
}

export function getImageCreditCosts() {
  return request.get("/image/credit-costs", { timeout: 15000 });
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
