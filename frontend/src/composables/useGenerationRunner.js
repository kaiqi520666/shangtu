import { ref } from "vue";
import { generateImage } from "@/api/image.js";
import { ensureEnoughImageCredits } from "@/composables/useImageCreditCosts.js";
import {
  createGenerationJob,
  getGenerationJob,
  listGenerationJobs,
  updateGenerationJob,
} from "@/api/generation.js";

const TITLE_DEBOUNCE_MS = 600;

export function useGenerationRunner({
  scenario,
  cards,
  toast,
  onJobCreated,
  resetSceneState,
  applyJobData,
  restoreCard,
  mediaUnit = "张",
} = {}) {
  const currentJobId = ref("");
  const currentTaskTitle = ref("");
  const historyTasks = ref([]);
  const showHistoryDrawer = ref(false);
  const historyLoading = ref(false);
  const jobLoading = ref(false);

  const {
    outputCards,
    genLogs,
    creatingBatch,
    generating,
    activeBatchRunId,
    startPollingCard,
    clearAllPollTimers,
    trackBatch,
    maybeFinishGenerating,
    makeId,
    TERMINAL_STATUSES,
  } = cards;

  let titleDebounceTimer = null;

  function updateCurrentJobTitle(title) {
    const trimmed = (title || "").trim();
    currentTaskTitle.value = title;
    if (!currentJobId.value) return;
    if (!trimmed) return;

    if (titleDebounceTimer) {
      clearTimeout(titleDebounceTimer);
    }
    titleDebounceTimer = setTimeout(async () => {
      try {
        const res = await updateGenerationJob(currentJobId.value, { title: trimmed });
        if (res.code !== 0) {
          toast.error("任务标题保存失败");
        }
      } catch {
        toast.error("任务标题保存失败");
      }
    }, TITLE_DEBOUNCE_MS);
  }

  async function ensureCurrentJob() {
    if (currentJobId.value) return currentJobId.value;
    try {
      const result = await createGenerationJob(scenario);
      if (result.code !== 0) {
        toast.error(result.message || "创建任务失败");
        return "";
      }
      currentJobId.value = result.data.job_id;
      currentTaskTitle.value = result.data.title;
      onJobCreated?.(currentJobId.value);
      return currentJobId.value;
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "创建任务失败");
      }
      return "";
    }
  }

  async function createNewTask() {
    if (generating.value) {
      toast.info("当前任务正在生成中，请稍后再新建任务");
      return false;
    }
    resetWorkspaceToDraft();
    return true;
  }

  function resetWorkspaceToDraft() {
    clearAllPollTimers();
    resetSceneState?.();
    outputCards.value = [];
    genLogs.value = [];
    creatingBatch.value = false;
    activeBatchRunId.value = "";
    currentJobId.value = "";
    currentTaskTitle.value = "";
  }

  async function loadHistoryTasks() {
    historyLoading.value = true;
    try {
      const result = await listGenerationJobs(scenario);
      if (result.code !== 0) {
        toast.error(result.message || "加载历史任务失败");
        historyTasks.value = [];
        return;
      }
      historyTasks.value = result.data || [];
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "加载历史任务失败");
      }
      historyTasks.value = [];
    } finally {
      historyLoading.value = false;
    }
  }

  async function loadGenerationJob(jobId) {
    if (!jobId) return false;
    if (generating.value) {
      toast.info("当前任务正在生成中，请稍后再切换任务");
      return false;
    }
    jobLoading.value = true;
    try {
      const result = await getGenerationJob(jobId);
      if (result.code !== 0) {
        toast.error(result.message || "任务不存在或无权限访问");
        return false;
      }
      const data = result.data || {};
      clearAllPollTimers();
      currentJobId.value = data.job_id;
      currentTaskTitle.value = data.title || "";
      activeBatchRunId.value = "";
      applyJobData?.(data);

      const items = Array.isArray(data.items) ? data.items : [];
      const restoredCards = items.map((item) => restoreCard(item));
      outputCards.value = restoredCards;

      const pendingCards = restoredCards.filter((card) => !TERMINAL_STATUSES.has(card.status));
      genLogs.value = restoredCards.length
        ? [`已恢复任务「${currentTaskTitle.value}」，共 ${restoredCards.length} ${mediaUnit}`]
        : [];

      if (pendingCards.length > 0) {
        const resumeBatchId = makeId();
        activeBatchRunId.value = resumeBatchId;
        trackBatch(resumeBatchId);
        pendingCards.forEach((card) => {
          card.batchRunId = resumeBatchId;
          startPollingCard(card);
        });
      } else {
        activeBatchRunId.value = "";
      }
      return true;
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "任务不存在或无权限访问");
      }
      return false;
    } finally {
      jobLoading.value = false;
    }
  }

  async function enqueueImageBatch({
    queue,
    imageUrls,
    ratio,
    resolution,
    snapshotPayload,
    createCard,
    buildPrompt,
    buildUserPrompt,
    buildSettingsSnapshot,
    initialLogs = [],
    repeatLog = "",
    getCreateLog,
    getFailLogName,
    allFailedMessage = "所有图片任务都创建失败，请稍后重试",
  }) {
    if (creatingBatch.value) {
      toast.info("正在创建图片任务，请稍候");
      return false;
    }

    creatingBatch.value = true;

    try {
      const hasEnoughCredits = await ensureEnoughImageCredits({
        quality: resolution,
        count: queue.length,
        toast,
        actionText: "本次生成",
      });
      if (!hasEnoughCredits) return false;

      const jobId = await ensureCurrentJob();
      if (!jobId) return false;

      const saveRes = await updateGenerationJob(jobId, {
        title: currentTaskTitle.value,
        ...snapshotPayload,
      });
      if (saveRes.code !== 0) {
        toast.error(saveRes.message || "保存任务配置失败，请稍后重试");
        return false;
      }

      const baseSortOrder = outputCards.value.length;
      const batchRunId = makeId();
      activeBatchRunId.value = batchRunId;
      trackBatch(batchRunId);
      if (genLogs.value.length === 0) {
        genLogs.value.push(...initialLogs);
      } else if (repeatLog) {
        genLogs.value.push(repeatLog);
      }

      const createdCards = queue.map((item, index) => {
        const sortOrder = baseSortOrder + index;
        const settingsSnapshot = buildSettingsSnapshot?.(item, { index, sortOrder }) || null;
        return {
          card: createCard({ item, index, sortOrder, batchRunId, settingsSnapshot }),
          item,
          settingsSnapshot,
        };
      });

      outputCards.value = [...createdCards.map((created) => created.card), ...outputCards.value];

      let successfullyEnqueued = 0;
      for (const { card, item, settingsSnapshot } of createdCards) {
        const prompt = buildPrompt?.(item, card) || "";
        const userPrompt = buildUserPrompt?.(item, card) || null;
        if (userPrompt) {
          card.userPrompt = userPrompt;
        }
        try {
          const result = await generateImage({
            prompt,
            user_prompt: userPrompt,
            image_urls: imageUrls,
            ratio,
            resolution,
            settings_snapshot: settingsSnapshot,
            job_id: jobId,
            type_id: card.typeId,
            title: card.strategyTitle,
            sort_order: card.sortOrder,
          });
          if (result.code !== 0) {
            card.status = "failed";
            card.errorMessage = result.message || "任务创建失败";
            genLogs.value.push(
              `[${getFailLogName?.(item, card) || card.strategyTitle}] 创建失败：${card.errorMessage}`,
            );
            continue;
          }
          card.taskId = result.data.task_id;
          genLogs.value.push(getCreateLog?.(item, card) || `正在生成 [${card.strategyTitle}]...`);
          startPollingCard(card);
          successfullyEnqueued += 1;
        } catch (error) {
          const status = error.response?.status;
          const message =
            status === 401
              ? "登录已过期，请重新登录"
              : error.response?.data?.message || "任务创建失败";
          card.status = "failed";
          card.errorMessage = message;
          genLogs.value.push(
            `[${getFailLogName?.(item, card) || card.strategyTitle}] 创建失败：${message}`,
          );
        }
      }

      genLogs.value.push(`已创建 ${successfullyEnqueued} 个图片任务`);
      if (successfullyEnqueued === 0) {
        maybeFinishGenerating(batchRunId, { silent: true });
        toast.error(allFailedMessage);
        return false;
      }

      maybeFinishGenerating(batchRunId);
      return true;
    } catch (error) {
      if (error?.response) {
        const status = error.response?.status;
        if (status === 401) {
          toast.error("登录已过期，请重新登录");
        } else {
          toast.error(error.response?.data?.message || "保存任务配置失败，请稍后重试");
        }
      } else {
        toast.error("任务创建失败，请稍后重试");
      }
      return false;
    } finally {
      creatingBatch.value = false;
    }
  }

  function cleanup() {
    clearAllPollTimers();
    if (titleDebounceTimer) {
      clearTimeout(titleDebounceTimer);
      titleDebounceTimer = null;
    }
  }

  return {
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    updateCurrentJobTitle,
    ensureCurrentJob,
    createNewTask,
    resetWorkspaceToDraft,
    loadHistoryTasks,
    loadGenerationJob,
    enqueueImageBatch,
    cleanup,
  };
}
