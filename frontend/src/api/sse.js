import { useAuthStore } from "@/stores/auth.js";
import { handleUnauthorized } from "./unauthorized.js";

function createApiError(message, status = 0) {
  const error = new Error(message);
  error.response = { status, data: { message } };
  return error;
}

async function readErrorResponse(response) {
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    // 非 JSON 错误由统一文案处理。
  }
  handleUnauthorized(response.status);
  throw createApiError(
    payload?.message || payload?.detail || "请求失败，请稍后重试",
    response.status,
  );
}

function dispatchEvent(eventName, dataLines, onChunk) {
  if (dataLines.length === 0) return false;
  let payload;
  try {
    payload = JSON.parse(dataLines.join("\n"));
  } catch {
    throw createApiError("流式响应格式异常");
  }
  if (eventName === "delta") {
    if (typeof payload.content !== "string") throw createApiError("流式响应格式异常");
    onChunk(payload.content);
  } else if (eventName === "error") {
    throw createApiError(payload.message || "AI 生成失败，请稍后重试");
  }
  return eventName === "done";
}

async function readEventStream(body, onChunk) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";
  let dataLines = [];

  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      while (buffer.includes("\n")) {
        const index = buffer.indexOf("\n");
        const line = buffer.slice(0, index).replace(/\r$/, "");
        buffer = buffer.slice(index + 1);
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
        if (!line) {
          if (dispatchEvent(eventName, dataLines, onChunk)) {
            await reader.cancel();
            return;
          }
          eventName = "message";
          dataLines = [];
        }
      }
      if (done) break;
    }
  } finally {
    reader.releaseLock();
  }
  throw createApiError("流式响应未正常结束");
}

export async function postSse(path, payload, { signal, onChunk }) {
  const authStore = useAuthStore();
  const baseURL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
  const response = await fetch(`${baseURL}${path}`, {
    method: "POST",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
      ...(authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok || !response.headers.get("content-type")?.includes("text/event-stream")) {
    await readErrorResponse(response);
  }
  if (!response.body) throw createApiError("浏览器不支持流式响应");
  await readEventStream(response.body, onChunk);
}
