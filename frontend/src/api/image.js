import request from "./request.js";

export function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request.post("/image/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });
}

export function analyzeImage({ image_url, platform = "" }) {
  return request.post("/image/analyze", { image_url, platform }, { timeout: 120000 });
}

export function generateProductImageStrategy({
  image_url,
  platform = "",
  language = "中文",
  product_input,
  module_ids,
}) {
  return request.post(
    "/image/product-image/strategy",
    { image_url, platform, language, product_input, module_ids },
    { timeout: 120000 },
  );
}

export function generateImage({
  prompt,
  image_url = null,
  ratio,
  resolution,
  job_id = null,
  type_id = null,
  title = null,
  sort_order = 0,
}) {
  return request.post(
    "/image/generate",
    { prompt, image_url, ratio, resolution, job_id, type_id, title, sort_order },
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

export function regenerateImageTask(taskId, editInstruction) {
  return request.post(
    `/image/task/${taskId}/regenerate`,
    { edit_instruction: editInstruction },
    { timeout: 60000 },
  );
}
