import { computed, ref, reactive } from "vue";
import { getImageTask } from "@/api/image.js";

const DEFAULT_POLL_INTERVAL_MS = 5000;
const TERMINAL_STATUSES = new Set(["done", "failed", "timeout"]);

function preloadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = resolve;
    img.onerror = reject;
    img.src = url;
  });
}

function makeId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function resolveSettingsSnapshot(rawSnapshot, existingSnapshot = null) {
  const snapshot =
    rawSnapshot && typeof rawSnapshot === "object" && !Array.isArray(rawSnapshot)
      ? rawSnapshot
      : null;
  const existing =
    existingSnapshot && typeof existingSnapshot === "object" && !Array.isArray(existingSnapshot)
      ? existingSnapshot
      : null;

  if (!existing && !snapshot) return null;
  return {
    ...existing,
    ...snapshot,
  };
}

function getPromptSnapshotUser(item) {
  const snapshot = item?.prompt_snapshot;
  return snapshot && typeof snapshot.user === "string" ? snapshot.user : "";
}

export function createBatchFinishedHandler({
  genLogs,
  toast,
  doneLog,
  successText,
  allFailedText,
  partialFailedText,
}) {
  return ({ total, failed }) => {
    genLogs?.value?.push(doneLog);
    if (failed === 0) {
      toast.success(successText);
    } else if (failed === total) {
      toast.error(allFailedText);
    } else {
      toast.info(
        typeof partialFailedText === "function"
          ? partialFailedText(failed)
          : partialFailedText,
      );
    }
  };
}

/**
 * 通用生成卡片状态 + 轮询引擎。
 * 与场景无关，可被商品套图 / 详情图 / 穿搭等场景 composable 复用。
 *
 * @param {Object} options
 * @param {Function} [options.getTask] - 单任务查询接口，默认查询图片任务
 * @param {number} [options.pollIntervalMs] - 轮询间隔，默认 5 秒
 * @param {string} [options.mediaLabel] - 日志和错误文案里的媒体名称，默认沿用通用文案
 * @param {boolean} [options.preloadResult] - done 后是否预加载结果资源，默认 true
 * @param {Function} [options.onCardDone] - 单卡完成回调 (card) => void
 * @param {Function} [options.onCardFailed] - 单卡失败/超时回调 (card) => void
 * @param {Function} [options.onBatchFinished] - 当前批次全部终态回调 ({ total, done, failed }) => void
 * @param {Function} [options.getLogPrefix] - 日志前缀 (card) => string，默认 card.strategyTitle
 */
export function useGenerationCards({
  getTask = getImageTask,
  pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
  mediaLabel = "",
  preloadResult = true,
  onCardDone,
  onCardFailed,
  onBatchFinished,
  getLogPrefix,
  genLogs: genLogsRef,
} = {}) {
  const outputCards = ref([]);
  const genLogs = genLogsRef || ref([]);
  const creatingBatch = ref(false);
  const runningCount = computed(
    () => outputCards.value.filter((card) => !TERMINAL_STATUSES.has(card.status)).length,
  );
  const generatedCount = computed(
    () => outputCards.value.filter((card) => card.status === "done").length,
  );
  const failedCount = computed(
    () =>
      outputCards.value.filter((card) => card.status === "failed" || card.status === "timeout")
        .length,
  );
  const jobTotal = computed(() => outputCards.value.length);
  const hasRunningTasks = computed(() => runningCount.value > 0);
  const generating = hasRunningTasks;
  const activeBatchRunId = ref("");

  const pollTimers = new Map();
  const pollInFlight = new Set();
  const pendingBatchIds = new Set();

  function logPrefix(card) {
    if (getLogPrefix) return getLogPrefix(card);
    return card.strategyTitle || card.typeId || "";
  }

  // --- 轮询引擎 ---

  function startPollingCard(card) {
    if (!card.taskId) return;
    stopPollingCard(card.id);
    card.stalledWarning = "";
    card.pollFailureCount = 0;
    const timer = window.setInterval(() => {
      pollCardOnce(card).catch(() => {});
    }, pollIntervalMs);
    pollTimers.set(card.id, timer);
    pollCardOnce(card).catch(() => {});
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

      // 处理本次响应前再校验一次终态，避免并发响应叠加导致 generatedCount 重复 +1
      if (TERMINAL_STATUSES.has(card.status)) {
        stopPollingCard(card.id);
        return;
      }

      const data = result.data || {};
      const status = data.status || "processing";
      const resultUrl = data.result_url || "";
      const displayUrl = data.thumb_url || resultUrl;
      const previewUrl = data.preview_url || resultUrl;
      const previousStatus = card.status;
      const previousProgress = typeof card.progress === "number" ? card.progress : 0;
      let taskAdvanced = status !== previousStatus;
      if (typeof data.progress === "number") {
        if (data.progress !== previousProgress) {
          taskAdvanced = true;
        }
        card.progress = data.progress;
      }
      if (typeof data.credit_cost === "number") {
        card.creditCost = data.credit_cost;
      }
      if (data.asset_id) {
        card.assetId = data.asset_id;
      }
      const promptSnapshotUser = getPromptSnapshotUser(data);
      if (promptSnapshotUser) {
        card.userPrompt = promptSnapshotUser;
      }
      const nextSettingsSnapshot = resolveSettingsSnapshot(
        data.settings_snapshot,
        card.settingsSnapshot,
      );
      if (nextSettingsSnapshot) {
        card.settingsSnapshot = nextSettingsSnapshot;
      }

      if (status === "done" && resultUrl) {
        // 防御：重新生成场景下，如果返回的 resultUrl 跟旧图一样，说明后端还没拿到新图
        if (card.previousResultUrl && resultUrl === card.previousResultUrl) {
          card.status = "processing";
        } else {
          stopPollingCard(card.id);
          if (preloadResult) {
            // 保持遮罩：预加载新图完成后再切换状态。视频等媒体可关闭预加载。
            try {
              await preloadImage(displayUrl);
            } catch {
              // 预加载失败也继续
            }
          }
          card.resultUrl = resultUrl;
          card.dataUrl = displayUrl;
          card.previewUrl = previewUrl;
          card.previousResultUrl = "";
          card.status = "done";
          card.stalledWarning = "";
          genLogs.value.push(`[${logPrefix(card)}] 已完成`);
          genLogs.value.push(`已完成 ${generatedCount.value}/${jobTotal.value}`);
          onCardDone?.(card);
        }
      } else if (status === "failed" || status === "timeout") {
        card.status = status;
        card.stalledWarning = "";
        const fallbackMessage =
          status === "timeout"
            ? `${mediaLabel}生成超时`
            : `${mediaLabel}生成失败`;
        card.errorMessage = data.error_message || fallbackMessage;
        genLogs.value.push(
          `[${logPrefix(card)}] ${status === "timeout" ? "超时" : "失败"}：${card.errorMessage}`,
        );
        stopPollingCard(card.id);
        onCardFailed?.(card);
      } else {
        // processing 或 done 但 result_url 仍未落库（worker 写入竞态/降级）
        card.status = status === "done" ? "processing" : status;
        if (taskAdvanced) {
          card.stalledWarning = "";
        }
      }

      maybeFinishBatch(card.batchRunId);
    } catch {
      card.pollFailureCount += 1;
      if (card.pollFailureCount >= 3) {
        card.stalledWarning = "连接异常，正在重试";
      }
    } finally {
      pollInFlight.delete(card.id);
    }
  }

  function stopPollingCard(cardId) {
    const timer = pollTimers.get(cardId);
    if (timer) {
      window.clearInterval(timer);
      pollTimers.delete(cardId);
    }
  }

  function clearAllPollTimers() {
    for (const timer of pollTimers.values()) {
      window.clearInterval(timer);
    }
    pollTimers.clear();
    pollInFlight.clear();
    pendingBatchIds.clear();
  }

  function trackBatch(batchRunId) {
    if (!batchRunId) return;
    pendingBatchIds.add(batchRunId);
  }

  function maybeFinishBatch(batchRunId, { silent = false } = {}) {
    if (!batchRunId || !pendingBatchIds.has(batchRunId)) return;
    const batchCards = outputCards.value.filter((card) => card.batchRunId === batchRunId);
    if (batchCards.length === 0) return;
    const allTerminal = batchCards.every((card) => TERMINAL_STATUSES.has(card.status));
    if (allTerminal) {
      pendingBatchIds.delete(batchRunId);
      const doneCount = batchCards.filter((card) => card.status === "done").length;
      const failedCount = batchCards.length - doneCount;
      if (!silent) {
        onBatchFinished?.({ total: batchCards.length, done: doneCount, failed: failedCount });
      }
    }
  }

  function maybeFinishGenerating(batchRunId, options) {
    if (batchRunId) {
      maybeFinishBatch(batchRunId, options);
      return;
    }
    for (const pendingBatchId of pendingBatchIds) {
      maybeFinishBatch(pendingBatchId, options);
    }
  }

  // --- 卡片工厂 ---

  /**
   * 创建一张 reactive 卡片对象
   */
  function createCard({
    typeId,
    strategyTitle,
    strategyContent,
    sortOrder,
    batchRunId,
    settingsSnapshot,
    userPrompt,
  }) {
    return reactive({
      id: makeId(),
      taskId: "",
      typeId: typeId || "",
      dataUrl: "",
      resultUrl: "",
      previewUrl: "",
      selected: false,
      status: "pending",
      strategyTitle: strategyTitle || "",
      strategyContent: strategyContent || "",
      errorMessage: "",
      sortOrder: sortOrder || 0,
      batchRunId: batchRunId || "",
      creditRefunded: false,
      userPrompt: userPrompt || "",
      settingsSnapshot: settingsSnapshot || null,
      assetId: "",
      progress: 0,
      stalledWarning: "",
      pollFailureCount: 0,
    });
  }

  function restoreCard(item, extra = {}) {
    return reactive({
      id: item.task_id,
      taskId: item.task_id,
      typeId: extra.typeId ?? item.type_id ?? "",
      dataUrl: item.thumb_url || item.result_url || "",
      resultUrl: item.result_url || "",
      previewUrl: item.preview_url || item.result_url || "",
      selected: false,
      status: item.status || "pending",
      strategyTitle: extra.strategyTitle ?? item.title ?? "",
      strategyContent: extra.strategyContent ?? "",
      errorMessage: item.error_message || "",
      sortOrder: item.sort_order || 0,
      batchRunId: "",
      creditRefunded: !!item.credit_refunded,
      userPrompt: extra.userPrompt ?? getPromptSnapshotUser(item),
      settingsSnapshot: resolveSettingsSnapshot(
        extra.settingsSnapshot ?? item.settings_snapshot,
      ),
      assetId: item.asset_id || "",
      progress: typeof item.progress === "number" ? item.progress : 0,
      stalledWarning: "",
      pollFailureCount: 0,
    });
  }

  // --- 清理 ---

  function cleanup() {
    clearAllPollTimers();
  }

  return {
    // 状态
    outputCards,
    genLogs,
    creatingBatch,
    hasRunningTasks,
    generating,
    generatedCount,
    runningCount,
    failedCount,
    jobTotal,
    activeBatchRunId,
    // 轮询
    startPollingCard,
    pollCardOnce,
    stopPollingCard,
    clearAllPollTimers,
    trackBatch,
    maybeFinishBatch,
    maybeFinishGenerating,
    // 工厂
    createCard,
    restoreCard,
    // 工具
    makeId,
    cleanup,
    // 常量
    TERMINAL_STATUSES,
  };
}
