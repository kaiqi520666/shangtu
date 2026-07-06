import request from "./request.js";

export function getAdminOverview() {
  return request.get("/admin/overview", { timeout: 15000 });
}

export function getAdminUsers(params = {}) {
  return request.get("/admin/users", { params, timeout: 15000 });
}

export function updateAdminUser(userId, payload) {
  return request.patch(`/admin/users/${userId}`, payload, { timeout: 15000 });
}

export function adjustAdminUserCredits(userId, payload) {
  return request.post(`/admin/users/${userId}/credits/adjust`, payload, { timeout: 15000 });
}

export function getAdminCreditOrders(params = {}) {
  return request.get("/admin/credit-orders", { params, timeout: 15000 });
}

export function getAdminCreditTransactions(params = {}) {
  return request.get("/admin/credit-transactions", { params, timeout: 15000 });
}

export function getAdminImageTasks(params = {}) {
  return request.get("/admin/image-tasks", { params, timeout: 15000 });
}

export function getAdminAssets(params = {}) {
  return request.get("/admin/image-tasks", {
    params: {
      ...params,
      status: params.status || "done",
    },
    timeout: 15000,
  });
}

export function getAdminSettings() {
  return request.get("/admin/settings", { timeout: 15000 });
}

export function updateAdminSettings(payload) {
  return request.put("/admin/settings", payload, { timeout: 15000 });
}

export function getAdminAuditLogs(params = {}) {
  return request.get("/admin/audit-logs", { params, timeout: 15000 });
}

export function getAdminPromptTemplates(params = {}) {
  return request.get("/admin/prompt-templates", { params, timeout: 15000 });
}

export function createAdminPromptTemplate(payload) {
  return request.post("/admin/prompt-templates", payload, { timeout: 15000 });
}

export function updateAdminPromptTemplate(templateId, payload) {
  return request.patch(`/admin/prompt-templates/${templateId}`, payload, { timeout: 15000 });
}

export function getAdminProductCatalog(params = {}) {
  return request.get("/admin/product-catalog", { params, timeout: 15000 });
}

export function updateAdminProductCatalog(catalogId, payload) {
  return request.patch(`/admin/product-catalog/${catalogId}`, payload, { timeout: 15000 });
}

export function getAdminOutfitModels(params = {}) {
  return request.get("/admin/outfit-models", { params, timeout: 15000 });
}

export function uploadAdminOutfitModel({ file, name, sortOrder }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", name || "");
  formData.append("sort_order", String(Number(sortOrder || 0)));
  return request.post("/admin/outfit-models/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });
}

export function updateAdminOutfitModel(modelId, payload) {
  return request.patch(`/admin/outfit-models/${modelId}`, payload, { timeout: 15000 });
}

export function getAdminHeygenAvatars(params = {}) {
  return request.get("/admin/heygen-avatars", { params, timeout: 15000 });
}

export function updateAdminHeygenAvatar(rowId, payload) {
  return request.patch(`/admin/heygen-avatars/${rowId}`, payload, { timeout: 15000 });
}

export function getAdminHeygenVoices(params = {}) {
  return request.get("/admin/heygen-voices", { params, timeout: 15000 });
}

export function updateAdminHeygenVoice(rowId, payload) {
  return request.patch(`/admin/heygen-voices/${rowId}`, payload, { timeout: 15000 });
}

export function syncAdminHeygenResources() {
  return request.post("/admin/heygen-resources/sync", {}, { timeout: 120000 });
}

export function getAdminHeygenTranslationLanguages(params = {}) {
  return request.get("/admin/heygen-translation-languages", { params, timeout: 15000 });
}

export function updateAdminHeygenTranslationLanguage(rowId, payload) {
  return request.patch(`/admin/heygen-translation-languages/${rowId}`, payload, { timeout: 15000 });
}

export function syncAdminHeygenTranslationLanguages() {
  return request.post("/admin/heygen-translation-languages/sync", {}, { timeout: 120000 });
}
