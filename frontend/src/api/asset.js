import request from "./request.js";

export function listAssets({ scenario = "", page = 1, page_size = 20 } = {}) {
  const params = { page, page_size };
  if (scenario) params.scenario = scenario;
  return request.get("/asset/list", { params, timeout: 15000 });
}

export function deleteAssets(taskIds) {
  return request.delete("/asset/batch", { data: { task_ids: taskIds }, timeout: 15000 });
}
