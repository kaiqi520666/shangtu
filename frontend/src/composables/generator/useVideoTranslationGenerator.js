import { computed, onBeforeUnmount, reactive, ref } from "vue";
import {
  createVideoTranslationTask,
  deleteVideoTranslationTask,
  getVideoTranslationConfig,
  getVideoTranslationDownloadUrl,
  pollVideoTranslationTask,
} from "@/api/videoTranslation.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/generator/useGenerationCards.js";
import { useMediaBatchRunner } from "@/composables/generator/batch/useMediaBatchRunner.js";
import { useCardActions } from "@/composables/useCardActions.js";
import {
  createVideoTranslationSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";
import { applyConsumptionMultiplier } from "@/utils/creditPricing.js";

const DEFAULT_SETTINGS = {
  targetLanguageId: "",
  qualityTier: "standard",
};

const QUALITY_TIER_LABELS = {
  standard: "标准翻译",
  premium: "高质翻译",
};

const VIDEO_POLL_INTERVAL_MS = 3000;

function createDefaultSettings() {
  return { ...DEFAULT_SETTINGS };
}

function formatDuration(seconds) {
  const value = Number(seconds || 0);
  if (value < 60) return `${value} 秒`;
  return `${Math.floor(value / 60)} 分 ${value % 60} 秒`;
}

export function useVideoTranslationGenerator({ toast, confirm, onJobCreated } = {}) {
  const settings = reactive(createDefaultSettings());
  const selectedVideo = ref(null);
  const languages = ref([]);
  const creditCosts = ref({ standard: 7, premium: 14 });
  const consumptionMultiplier = ref(1);

  const cards = useGenerationCards({
    getTask: pollVideoTranslationTask,
    pollIntervalMs: VIDEO_POLL_INTERVAL_MS,
    mediaLabel: "视频",
    preloadResult: false,
    getLogPrefix: (card) => card.strategyTitle || getVideoTranslationModuleName(card.typeId),
    onCardDone: (card) => {
      card.progress = 100;
    },
    onBatchFinished: createBatchFinishedHandler({
      genLogs: null,
      toast,
      doneLog: "视频翻译任务已结束",
      successText: "视频翻译完成",
      allFailedText: "视频翻译失败，请稍后重试",
      partialFailedText: (failed) => `${failed} 个视频翻译失败，其余已完成`,
    }),
  });

  const {
    outputCards,
    genLogs,
    creatingBatch,
    generating,
    runningCount,
    generatedCount,
    failedCount,
    jobTotal,
    stopPollingCard,
  } = cards;

  const runner = useMediaBatchRunner({
    scenario: "video_translation",
    cards,
    toast,
    onJobCreated,
    mediaUnit: "个",
    resetSceneState() {
      Object.assign(settings, createDefaultSettings());
      selectedVideo.value = null;
    },
    applyJobData(data) {
      restoreVideoTranslationJobData(data);
    },
    restoreCard(item) {
      const snapshot = item.settings_snapshot || null;
      const scene = getSnapshotScene(snapshot);
      return cards.restoreCard(item, {
        strategyTitle: item.title || getVideoTranslationModuleName(item.type_id),
        strategyContent: scene.targetLanguageDisplayNameZh || scene.targetLanguageName || "",
        settingsSnapshot: snapshot,
      });
    },
  });

  const {
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    updateCurrentJobTitle,
    createNewTask,
    resetWorkspaceToDraft,
    loadHistoryTasks,
    loadGenerationJob,
    enqueueMediaBatch,
    cleanup,
  } = runner;

  const actions = useCardActions({
    outputCards,
    currentTaskTitle,
    getCardName: (card) => card.strategyTitle || getVideoTranslationModuleName(card.typeId),
    getDownloadUrl: (card) => getVideoTranslationDownloadUrl(card.taskId),
    toast,
    mediaLabel: "视频",
    mediaUnit: "个",
    archiveName: "视频翻译",
  });

  const {
    downloading,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleMedia: downloadSingleVideo,
  } = actions;

  const selectedLanguage = computed(() =>
    languages.value.find((item) => item.id === settings.targetLanguageId) || null,
  );
  const languageOptions = computed(() =>
    languages.value.map((item) => ({
      value: item.id,
      label: item.display_name_zh || item.name,
      description: item.name,
    })),
  );
  const qualityOptions = computed(() => [
    {
      value: "standard",
      label: "标准翻译",
      description: `${creditCosts.value.standard || 0} 积分/秒`,
    },
    {
      value: "premium",
      label: "高质翻译",
      description: `${creditCosts.value.premium || 0} 积分/秒`,
    },
  ]);
  const durationSeconds = computed(() => Number(selectedVideo.value?.durationSeconds || 0));
  const estimatedCreditCost = computed(() => applyConsumptionMultiplier(
    durationSeconds.value * Number(creditCosts.value[settings.qualityTier] || 0),
    consumptionMultiplier.value,
  ));
  const feeText = computed(() => {
    if (!durationSeconds.value) return "";
    const unitCost = Number(creditCosts.value[settings.qualityTier] || 0);
    return `预计时长 ${formatDuration(durationSeconds.value)}，${unitCost} 积分/秒，预计扣费 ${estimatedCreditCost.value} 积分`;
  });
  const canGenerate = computed(() => {
    if (creatingBatch.value) return false;
    if (!selectedVideo.value?.url || selectedVideo.value?.uploading) return false;
    if (!durationSeconds.value) return false;
    if (!settings.targetLanguageId) return false;
    return Boolean(settings.qualityTier);
  });
  const generateButtonText = computed(() => {
    if (creatingBatch.value) return "创建任务中...";
    if (selectedVideo.value?.uploading) return "视频上传中...";
    return "开始翻译";
  });

  async function loadConfig() {
    try {
      const result = await getVideoTranslationConfig();
      if (result.code !== 0) {
        toast?.error?.(result.message || "加载视频翻译配置失败");
        return;
      }
      languages.value = result.data?.languages || [];
      consumptionMultiplier.value = Number(result.data?.consumption_multiplier || 1);
      creditCosts.value = {
        ...creditCosts.value,
        ...result.data?.credit_costs,
      };
      if (!settings.targetLanguageId && languages.value.length > 0) {
        settings.targetLanguageId = languages.value[0].id;
      }
    } catch {
      toast?.error?.("加载视频翻译配置失败");
    }
  }

  function updateSettings(nextSettings) {
    Object.assign(settings, nextSettings);
  }

  function showNotice(message) {
    if (message && typeof message === "object") {
      const type = message.type === "error" ? "error" : message.type === "success" ? "success" : "info";
      const text = String(message.message || "").trim();
      if (text) toast?.[type]?.(text);
      return;
    }
    toast?.info?.(message);
  }

  function buildSettingsSnapshot() {
    const language = selectedLanguage.value;
    const unitCost = Number(creditCosts.value[settings.qualityTier] || 0);
    return createVideoTranslationSettingsSnapshot({
      videoUrl: selectedVideo.value?.url || "",
      targetLanguageId: language?.id || "",
      targetLanguageName: language?.name || "",
      targetLanguageDisplayNameZh: language?.display_name_zh || "",
      qualityTier: settings.qualityTier,
      durationSeconds: durationSeconds.value,
      perSecondCost: unitCost,
      creditCost: estimatedCreditCost.value,
      source: selectedVideo.value?.source || "upload",
      assetTaskId: selectedVideo.value?.assetTaskId || "",
    });
  }

  async function generateVideoTranslation() {
    if (!selectedVideo.value?.url) {
      toast?.info?.("请先选择视频");
      return;
    }
    if (selectedVideo.value.uploading) {
      toast?.info?.("视频上传中，请稍后再提交");
      return;
    }
    if (!durationSeconds.value) {
      toast?.info?.("无法获取视频时长，请重新上传或选择视频");
      return;
    }
    if (!selectedLanguage.value) {
      toast?.info?.("请先选择目标语言");
      return;
    }

    const title = (currentTaskTitle.value || "").trim() || "视频翻译";
    const settingsSnapshot = buildSettingsSnapshot();
    const queue = [{ qualityTier: settings.qualityTier }];

    await enqueueMediaBatch({
      queue,
      snapshotPayload: {
        settings: settingsSnapshot,
        input_text: selectedLanguage.value.display_name_zh || selectedLanguage.value.name,
      },
      initialLogs: [`[${title}] 创建视频翻译任务`],
      repeatLog: `[${title}] 创建视频翻译任务`,
      buildSettingsSnapshot: () => settingsSnapshot,
      createCard({ item, sortOrder, batchRunId, settingsSnapshot: snapshot }) {
        return createCard({
          typeId: item.qualityTier,
          title,
          settingsSnapshot: snapshot,
          sortOrder,
          batchRunId,
        });
      },
      createTask({ item, jobId }) {
        return createVideoTranslationTask({
          job_id: jobId,
          title,
          video_url: selectedVideo.value.url,
          duration_seconds: durationSeconds.value,
          target_language_id: selectedLanguage.value.id,
          quality_tier: item.qualityTier,
          source: selectedVideo.value.source || "upload",
          asset_task_id: selectedVideo.value.assetTaskId || undefined,
        });
      },
      getCreateLog: () => `[${title}] 已进入队列`,
      getFailLogName: () => title,
      allFailedMessage: "视频翻译任务创建失败，请稍后重试",
      saveErrorMessage: "保存视频翻译任务配置失败",
      taskIdMissingMessage: "视频翻译任务创建失败：后端未返回任务 ID",
      insertCards: "after-success",
      preferCreateErrorAsToast: true,
    });
  }

  function createCard({
    typeId,
    title,
    settingsSnapshot,
    sortOrder = outputCards.value.length,
    batchRunId = "",
  }) {
    const scene = getSnapshotScene(settingsSnapshot);
    const card = cards.createCard({
      typeId,
      strategyTitle: title || getVideoTranslationModuleName(typeId),
      strategyContent: scene.targetLanguageDisplayNameZh || scene.targetLanguageName || "",
      sortOrder,
      batchRunId,
      userPrompt: scene.targetLanguageDisplayNameZh || scene.targetLanguageName || "",
      settingsSnapshot,
    });
    card.progress = 10;
    return card;
  }

  function restoreVideoTranslationJobData(data) {
    const snapshot = data.settings || null;
    const scene = getSnapshotScene(snapshot);
    settings.targetLanguageId = scene.targetLanguageId || "";
    settings.qualityTier = scene.qualityTier || "standard";
    selectedVideo.value = scene.videoUrl
      ? {
          id: `restore_${scene.videoUrl}`,
          previewUrl: scene.videoUrl,
          url: scene.videoUrl,
          uploading: false,
          error: "",
          source: scene.source || "asset",
          assetTaskId: scene.assetTaskId || "",
          durationSeconds: Number(scene.durationSeconds || 0),
        }
      : null;
  }

  async function removeCard(card) {
    if (!card?.taskId) {
      outputCards.value = outputCards.value.filter((item) => item.id !== card?.id);
      return;
    }
    const ok = await confirm?.open?.({
      title: "删除视频",
      message: "确定删除这个视频翻译任务吗？视频不会立即从存储中物理删除。",
      confirmText: "删除",
      cancelText: "取消",
      tone: "danger",
    });
    if (ok === false) return;

    try {
      const result = await deleteVideoTranslationTask(card.taskId);
      if (result.code !== 0) {
        toast?.error?.(result.message || "删除失败");
        return;
      }
      outputCards.value = outputCards.value.filter((item) => item.id !== card.id);
      stopPollingCard(card.id);
      toast?.success?.("视频已删除");
    } catch {
      toast?.error?.("删除失败，请稍后重试");
    }
  }

  function getVideoTranslationModuleName(typeId) {
    return QUALITY_TIER_LABELS[typeId] || "视频翻译";
  }

  onBeforeUnmount(() => {
    cleanup();
  });

  return {
    settings,
    selectedVideo,
    languages,
    creditCosts,
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    outputCards,
    genLogs,
    creatingBatch,
    generating,
    runningCount,
    generatedCount,
    failedCount,
    jobTotal,
    downloading,
    selectedCardsCount,
    languageOptions,
    qualityOptions,
    durationSeconds,
    estimatedCreditCost,
    feeText,
    canGenerate,
    generateButtonText,
    loadConfig,
    updateSettings,
    showNotice,
    generateVideoTranslation,
    updateCurrentJobTitle,
    createNewTask,
    resetWorkspaceToDraft,
    loadHistoryTasks,
    loadGenerationJob,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleVideo,
    removeCard,
    getVideoTranslationModuleName,
  };
}
