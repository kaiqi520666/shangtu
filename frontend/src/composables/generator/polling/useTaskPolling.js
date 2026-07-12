export const TERMINAL_STATUSES = new Set(["done", "failed", "timeout"]);

function preloadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = resolve;
    img.onerror = reject;
    img.src = url;
  });
}

export function resolveSettingsSnapshot(rawSnapshot, existingSnapshot = null) {
  const snapshot = rawSnapshot && typeof rawSnapshot === "object" && !Array.isArray(rawSnapshot)
    ? rawSnapshot
    : null;
  const existing = existingSnapshot && typeof existingSnapshot === "object" && !Array.isArray(existingSnapshot)
    ? existingSnapshot
    : null;
  if (!existing && !snapshot) return null;
  return { ...existing, ...snapshot };
}

export function getPromptSnapshotUser(item) {
  const snapshot = item?.prompt_snapshot;
  return snapshot && typeof snapshot.user === "string" ? snapshot.user : "";
}

export function useTaskPolling({
  getTask,
  pollIntervalMs,
  preloadResult,
  mediaLabel,
  genLogs,
  generatedCount,
  jobTotal,
  logPrefix,
  onCardDone,
  onCardFailed,
  onCardSettled,
}) {
  const pollTimers = new Map();
  const pollInFlight = new Set();

  function stopPollingCard(cardId) {
    const timer = pollTimers.get(cardId);
    if (!timer) return;
    window.clearInterval(timer);
    pollTimers.delete(cardId);
  }

  function startPollingCard(card) {
    if (!card.taskId) return;
    stopPollingCard(card.id);
    card.stalledWarning = "";
    card.pollFailureCount = 0;
    const timer = window.setInterval(() => pollCardOnce(card), pollIntervalMs);
    pollTimers.set(card.id, timer);
    pollCardOnce(card);
  }

  async function applyTaskResult(card, data) {
    const status = data.status || "processing";
    const resultUrl = data.result_url || "";
    const displayUrl = data.thumb_url || resultUrl;
    const previewUrl = data.preview_url || resultUrl;
    if (typeof data.progress === "number") card.progress = data.progress;
    if (typeof data.credit_cost === "number") card.creditCost = data.credit_cost;
    if (data.asset_id) card.assetId = data.asset_id;
    const prompt = getPromptSnapshotUser(data);
    if (prompt) card.userPrompt = prompt;
    const settings = resolveSettingsSnapshot(data.settings_snapshot, card.settingsSnapshot);
    if (settings) card.settingsSnapshot = settings;

    if (status === "done" && resultUrl) {
      if (card.previousResultUrl && resultUrl === card.previousResultUrl) {
        card.status = "processing";
        return;
      }
      stopPollingCard(card.id);
      if (preloadResult) {
        try {
          await preloadImage(displayUrl);
        } catch {
          // 资源预加载失败不影响服务端任务终态。
        }
      }
      Object.assign(card, {
        resultUrl,
        dataUrl: displayUrl,
        previewUrl,
        previousResultUrl: "",
        status: "done",
        stalledWarning: "",
      });
      genLogs.value.push(`[${logPrefix(card)}] 已完成`);
      genLogs.value.push(`已完成 ${generatedCount.value}/${jobTotal.value}`);
      onCardDone?.(card);
      return;
    }
    if (status === "failed" || status === "timeout") {
      card.status = status;
      card.stalledWarning = "";
      card.errorMessage = data.error_message || (status === "timeout" ? `${mediaLabel}生成超时` : `${mediaLabel}生成失败`);
      genLogs.value.push(`[${logPrefix(card)}] ${status === "timeout" ? "超时" : "失败"}：${card.errorMessage}`);
      stopPollingCard(card.id);
      onCardFailed?.(card);
      return;
    }
    card.status = status === "done" ? "processing" : status;
  }

  async function pollCardOnce(card) {
    if (!card.taskId) return;
    if (TERMINAL_STATUSES.has(card.status)) {
      stopPollingCard(card.id);
      return;
    }
    if (pollInFlight.has(card.id)) return;
    pollInFlight.add(card.id);
    try {
      const result = await getTask(card.taskId);
      if (result.code !== 0) throw new Error(result.message || "任务状态查询失败");
      card.pollFailureCount = 0;
      card.stalledWarning = "";
      if (TERMINAL_STATUSES.has(card.status)) return stopPollingCard(card.id);
      await applyTaskResult(card, result.data || {});
      onCardSettled?.(card);
    } catch {
      card.pollFailureCount += 1;
      if (card.pollFailureCount >= 3) card.stalledWarning = "连接异常，正在重试";
    } finally {
      pollInFlight.delete(card.id);
    }
  }

  function clearPollTimers() {
    for (const timer of pollTimers.values()) window.clearInterval(timer);
    pollTimers.clear();
    pollInFlight.clear();
  }

  return { startPollingCard, pollCardOnce, stopPollingCard, clearPollTimers };
}
