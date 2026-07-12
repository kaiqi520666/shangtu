import { computed, ref, reactive } from "vue";
import { getImageTask } from "@/api/image.js";
import {
  getPromptSnapshotUser,
  resolveSettingsSnapshot,
  TERMINAL_STATUSES,
  useTaskPolling,
} from "@/composables/generator/polling/useTaskPolling.js";

const DEFAULT_POLL_INTERVAL_MS = 5000;

function makeId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
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

  const pendingBatchIds = new Set();

  function logPrefix(card) {
    if (getLogPrefix) return getLogPrefix(card);
    return card.strategyTitle || card.typeId || "";
  }

  const {
    startPollingCard,
    pollCardOnce,
    stopPollingCard,
    clearPollTimers,
  } = useTaskPolling({
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
    onCardSettled: (card) => maybeFinishBatch(card.batchRunId),
  });

  function clearAllPollTimers() {
    clearPollTimers();
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
