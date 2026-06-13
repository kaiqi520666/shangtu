import { ref, reactive } from "vue";
import { getImageTask } from "@/api/image.js";

const POLL_INTERVAL_MS = 5000;
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

/**
 * 通用生图卡片状态 + 轮询引擎。
 * 与场景无关，可被商品套图 / 详情图 / 穿搭等场景 composable 复用。
 *
 * @param {Object} options
 * @param {Function} [options.onCardDone] - 单卡完成回调 (card) => void
 * @param {Function} [options.onCardFailed] - 单卡失败/超时回调 (card) => void
 * @param {Function} [options.onBatchFinished] - 当前批次全部终态回调 ({ total, done, failed }) => void
 * @param {Function} [options.getLogPrefix] - 日志前缀 (card) => string，默认 card.strategyTitle
 */
export function useGenerationCards({
  onCardDone,
  onCardFailed,
  onBatchFinished,
  getLogPrefix,
} = {}) {
  const outputCards = ref([]);
  const genLogs = ref([]);
  const generating = ref(false);
  const generatedCount = ref(0);
  const jobTotal = ref(0);
  const activeBatchRunId = ref("");

  const pollTimers = new Map();
  const pollInFlight = new Set();

  function logPrefix(card) {
    if (getLogPrefix) return getLogPrefix(card);
    return card.strategyTitle || card.typeId || "";
  }

  // --- 轮询引擎 ---

  function startPollingCard(card) {
    if (!card.taskId) return;
    stopPollingCard(card.id);
    const timer = window.setInterval(() => {
      pollCardOnce(card).catch(() => {});
    }, POLL_INTERVAL_MS);
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
      const result = await getImageTask(card.taskId);
      if (result.code !== 0) return;

      // 处理本次响应前再校验一次终态，避免并发响应叠加导致 generatedCount 重复 +1
      if (TERMINAL_STATUSES.has(card.status)) {
        stopPollingCard(card.id);
        return;
      }

      const data = result.data || {};
      const status = data.status || "processing";
      const resultUrl = data.result_url || "";
      if (typeof data.user_prompt === "string") {
        card.userPrompt = data.user_prompt;
      }

      if (status === "done" && resultUrl) {
        // 防御：重新生成场景下，如果返回的 resultUrl 跟旧图一样，说明后端还没拿到新图
        if (card.previousResultUrl && resultUrl === card.previousResultUrl) {
          card.status = "processing";
        } else {
          stopPollingCard(card.id);
          // 保持遮罩：预加载新图完成后再切换状态
          try {
            await preloadImage(resultUrl);
          } catch {
            // 预加载失败也继续
          }
          card.resultUrl = resultUrl;
          card.dataUrl = resultUrl;
          card.previousResultUrl = "";
          card.status = "done";
          generatedCount.value += 1;
          genLogs.value.push(`[${logPrefix(card)}] 已完成`);
          genLogs.value.push(`已完成 ${generatedCount.value}/${jobTotal.value}`);
          onCardDone?.(card);
        }
      } else if (status === "failed" || status === "timeout") {
        card.status = status;
        card.errorMessage = data.error_message || (status === "timeout" ? "生成超时" : "生成失败");
        genLogs.value.push(
          `[${logPrefix(card)}] ${status === "timeout" ? "超时" : "失败"}：${card.errorMessage}`,
        );
        stopPollingCard(card.id);
        onCardFailed?.(card);
      } else {
        // processing 或 done 但 result_url 仍未落库（worker 写入竞态/降级）
        card.status = status === "done" ? "processing" : status;
      }

      maybeFinishGenerating();
    } catch {
      // 单次轮询异常不停止该任务，等下一次 tick
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
  }

  function maybeFinishGenerating() {
    if (!generating.value) return;
    const batchId = activeBatchRunId.value;
    const batchCards = batchId
      ? outputCards.value.filter((card) => card.batchRunId === batchId)
      : outputCards.value;
    if (batchCards.length === 0) return;
    const allTerminal = batchCards.every((card) => TERMINAL_STATUSES.has(card.status));
    if (allTerminal) {
      generating.value = false;
      const doneCount = batchCards.filter((card) => card.status === "done").length;
      const failedCount = batchCards.length - doneCount;
      onBatchFinished?.({ total: batchCards.length, done: doneCount, failed: failedCount });
    }
  }

  // --- 卡片工厂 ---

  /**
   * 创建一张 reactive 卡片对象
   */
  function createCard({ typeId, strategyTitle, strategyContent, sortOrder, batchRunId }) {
    return reactive({
      id: makeId(),
      taskId: "",
      typeId: typeId || "",
      dataUrl: "",
      resultUrl: "",
      selected: true,
      status: "pending",
      strategyTitle: strategyTitle || "",
      strategyContent: strategyContent || "",
      errorMessage: "",
      sortOrder: sortOrder || 0,
      batchRunId: batchRunId || "",
      creditRefunded: false,
      userPrompt: "",
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
    generating,
    generatedCount,
    jobTotal,
    activeBatchRunId,
    // 轮询
    startPollingCard,
    pollCardOnce,
    stopPollingCard,
    clearAllPollTimers,
    maybeFinishGenerating,
    // 工厂
    createCard,
    // 工具
    makeId,
    cleanup,
    // 常量
    TERMINAL_STATUSES,
  };
}
