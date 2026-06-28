import request from "./request.js";

export function listAssets({ scenario = "", media_type = "", page = 1, page_size = 20 } = {}) {
  const params = { page, page_size };
  if (scenario) params.scenario = scenario;
  if (media_type) params.media_type = media_type;
  return request.get("/asset/list", { params, timeout: 15000 });
}

export function deleteAssets(taskIds, mediaType = "") {
  return request.delete("/asset/batch", {
    data: { task_ids: taskIds, media_type: mediaType || null },
    timeout: 15000,
  });
}
