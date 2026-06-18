import { computed, onBeforeUnmount, reactive, ref } from "vue";
import { generateVideo, getVideoCreditCosts, getVideoDownloadUrl, getVideoTask } from "@/api/video.js";
import { updateGenerationJob } from "@/api/generation.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import {
  defaultVideoCreditCosts,
  getVideoDemoType,
  videoDemoTypes,
  videoLanguageOptions,
  videoMarketOptions,
  videoSizeOptions,
} from "@/constants/productVideo.js";

const POLL_INTERVAL_MS = 3000;
const TERMINAL_STATUSES = new Set(["done", "failed", "timeout"]);

function makeId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function getOptionLabel(options, value) {
  return options.find((item) => item.value === value)?.label || value;
}

function getSelectedSize(sizePreset) {
  return videoSizeOptions.find((item) => item.value === sizePreset) || videoSizeOptions[0];
}

function buildSettingsSnapshot(settings) {
  const selectedType = getVideoDemoType(settings.videoType);
  const selectedSize = getSelectedSize(settings.sizePreset);
  return {
    scenario: "product_video",
    type_id: settings.videoType,
    title: selectedType.title,
    input_mode: selectedType.inputMode,
    market: settings.market,
    market_label: getOptionLabel(videoMarketOptions, settings.market),
    language: settings.language,
    language_label: getOptionLabel(videoLanguageOptions, settings.language),
    size_preset: settings.sizePreset,
    aspect_ratio: selectedSize.aspectRatio,
    duration: settings.duration,
    resolution: settings.resolution,
    product_input: settings.productInput,
  };
}

function getRequiredImageMessage(inputMode, count) {
  if (inputMode === "first_frame" && count !== 1) return "请上传 1 张首帧图";
  if (inputMode === "first_last_frame" && count !== 2) return "请上传开始图和结束图";
  if (inputMode === "reference_images" && (count < 1 || count > 9)) {
    return "请上传 1-9 张参考图";
  }
  return "";
}

export function useProductVideoGenerator({ toast, onJobCreated } = {}) {
  const settings = reactive({
    videoType: videoDemoTypes[0].typeId,
    inputMode: videoDemoTypes[0].inputMode,
    market: "global",
    language: "english",
    sizePreset: "tiktok_9_16",
    duration: 6,
    resolution: "720p",
    productInput: "",
  });
  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);
  const creditCosts = ref({ ...defaultVideoCreditCosts });
  const outputCards = ref([]);
  const genLogs = ref([]);
  const creatingBatch = ref(false);
  const activeBatchRunId = ref("");

  const pollTimers = new Map();
  const pollInFlight = new Set();

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
  const generating = computed(() => runningCount.value > 0);

  async function loadCreditCosts() {
    try {
      const result = await getVideoCreditCosts();
      if (result.code === 0 && result.data?.costs) {
        creditCosts.value = {
          ...defaultVideoCreditCosts,
          ...result.data.costs,
        };
      }
    } catch {
      toast?.info?.("视频扣费配置读取失败，已使用默认配置");
    }
  }

  function updateSettings(nextSettings) {
    Object.assign(settings, nextSettings);
  }

  function showNotice(message) {
    toast?.info?.(message);
  }

  const cardsAdapter = {
    outputCards,
    genLogs,
    creatingBatch,
    generating,
    activeBatchRunId,
    startPollingCard,
    clearAllPollTimers,
    trackBatch() {},
    maybeFinishGenerating() {},
    makeId,
    TERMINAL_STATUSES,
  };

  const runner = useGenerationRunner({
    scenario: "product_video",
    cards: cardsAdapter,
    toast,
    onJobCreated,
    mediaUnit: "个",
    resetSceneState() {
      uploadedImages.value = [];
      mainImageIndex.value = 0;
      settings.videoType = videoDemoTypes[0].typeId;
      settings.inputMode = videoDemoTypes[0].inputMode;
      settings.market = "global";
      settings.language = "english";
      settings.sizePreset = "tiktok_9_16";
      settings.duration = 6;
      settings.resolution = "720p";
      settings.productInput = "";
    },
    applyJobData(data) {
      restoreVideoJobData(data);
    },
    restoreCard(item) {
      return createCard({
        taskId: item.task_id,
        typeId: item.type_id,
        title: item.title || getVideoModuleName(item.type_id),
        settingsSnapshot: item.settings_snapshot || null,
        creditCost: item.credit_cost || 0,
        status: item.status || "pending",
        resultUrl: item.result_url || "",
        errorMessage: item.error_message || "",
        progress: item.progress || 0,
        sortOrder: item.sort_order || 0,
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
    ensureCurrentJob,
    createNewTask,
    resetWorkspaceToDraft,
    loadHistoryTasks,
    loadGenerationJob,
  } = runner;

  const actions = useCardActions({
    outputCards,
    currentTaskTitle,
    getCardName: (card) => card.strategyTitle || getVideoModuleName(card.typeId),
    getDownloadUrl: (card) => getVideoDownloadUrl(card.taskId),
    mediaLabel: "视频",
    mediaUnit: "个",
    archiveName: "商品视频",
    toast,
  });

  const {
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleMedia: downloadSingleVideo,
  } = actions;

  function createCard({
    taskId,
    typeId,
    title,
    settingsSnapshot,
    creditCost,
    status = "pending",
    resultUrl = "",
    errorMessage = "",
    progress = 0,
    sortOrder = outputCards.value.length,
  }) {
    return reactive({
      id: makeId(),
      taskId,
      typeId,
      dataUrl: resultUrl,
      resultUrl,
      selected: false,
      status,
      strategyTitle: title || "商品视频",
      strategyContent: settingsSnapshot?.product_input || "",
      errorMessage,
      sortOrder,
      batchRunId: "",
      creditCost,
      userPrompt: settingsSnapshot?.product_input || "",
      settingsSnapshot,
      progress,
    });
  }

  function restoreVideoJobData(data) {
    const s = data.settings || {};
    if (typeof s.type_id === "string") {
      settings.videoType = s.type_id;
      settings.inputMode = getVideoDemoType(s.type_id).inputMode;
    }
    if (typeof s.input_mode === "string") settings.inputMode = s.input_mode;
    if (typeof s.market === "string") settings.market = s.market;
    if (typeof s.language === "string") settings.language = s.language;
    if (typeof s.size_preset === "string") settings.sizePreset = s.size_preset;
    if (typeof s.duration === "number") settings.duration = s.duration;
    if (typeof s.resolution === "string") settings.resolution = s.resolution;
    settings.productInput = data.input_text || s.product_input || "";
    if (Array.isArray(data.source_images)) {
      uploadedImages.value = data.source_images.map((img) => ({
        ...img,
        previewUrl: img?.url || img?.previewUrl || "",
      }));
    } else {
      uploadedImages.value = [];
    }
    mainImageIndex.value = 0;
  }

  async function generateProductVideo() {
    if (generating.value || creatingBatch.value) {
      toast?.info?.("当前视频任务还在生成中");
      return;
    }

    const selectedType = getVideoDemoType(settings.videoType);
    const imageUrls = uploadedImages.value.map((item) => item?.url).filter(Boolean);
    const requirementMessage = getRequiredImageMessage(selectedType.inputMode, imageUrls.length);
    if (requirementMessage) {
      toast?.info?.(requirementMessage);
      return;
    }
    if (uploadedImages.value.some((item) => item?.uploading)) {
      toast?.info?.("素材还在上传中，请稍等");
      return;
    }

    const settingsSnapshot = buildSettingsSnapshot(settings);
    creatingBatch.value = true;
    genLogs.value.push(`[${selectedType.title}] 创建视频任务`);

    try {
      const jobId = await ensureCurrentJob();
      if (!jobId) return;
      const saveRes = await updateGenerationJob(jobId, {
        title: currentTaskTitle.value,
        settings: settingsSnapshot,
        source_images: uploadedImages.value.map((img) => ({
          id: img.id,
          url: img.url,
          objectKey: img.objectKey,
          contentType: img.contentType,
          size: img.size,
          previewUrl: img.url || img.previewUrl,
        })),
        input_text: settings.productInput,
        structure: [selectedType],
      });
      if (saveRes.code !== 0) {
        toast?.error?.(saveRes.message || "保存视频任务配置失败");
        return;
      }

      const result = await generateVideo({
        type_id: selectedType.typeId,
        title: selectedType.title,
        input_mode: selectedType.inputMode,
        image_urls: imageUrls,
        user_prompt: settings.productInput,
        duration: settings.duration,
        resolution: settings.resolution,
        aspect_ratio: settingsSnapshot.aspect_ratio,
        settings_snapshot: settingsSnapshot,
        sort_order: outputCards.value.length,
        job_id: jobId,
      });

      if (result.code !== 0) {
        toast?.error?.(result.message || "视频任务创建失败");
        return;
      }

      const taskId = result.data?.task_id;
      if (!taskId) {
        toast?.error?.("视频任务创建失败：后端未返回任务 ID");
        return;
      }

      const card = createCard({
        taskId,
        typeId: selectedType.typeId,
        title: selectedType.title,
        settingsSnapshot,
        creditCost: result.data?.credit_cost || 0,
      });
      outputCards.value.unshift(card);
      genLogs.value.push(`[${selectedType.title}] 已进入队列`);
      startPollingCard(card);
    } catch {
      toast?.error?.("视频任务创建失败，请稍后重试");
    } finally {
      creatingBatch.value = false;
    }
  }

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
    if (!card.taskId || TERMINAL_STATUSES.has(card.status)) {
      stopPollingCard(card.id);
      return;
    }
    if (pollInFlight.has(card.id)) return;
    pollInFlight.add(card.id);
    try {
      const result = await getVideoTask(card.taskId);
      if (result.code !== 0) return;
      const data = result.data || {};
      const status = data.status || "processing";
      const resultUrl = data.result_url || "";

      if (data.settings_snapshot) {
        card.settingsSnapshot = {
          ...(card.settingsSnapshot || {}),
          ...data.settings_snapshot,
        };
      }
      if (typeof data.user_prompt === "string") {
        card.userPrompt = data.user_prompt;
      }
      if (typeof data.progress === "number") {
        card.progress = data.progress;
      }

      if (status === "done" && resultUrl) {
        stopPollingCard(card.id);
        card.resultUrl = resultUrl;
        card.dataUrl = resultUrl;
        card.status = "done";
        card.progress = 100;
        genLogs.value.push(`[${card.strategyTitle}] 已完成`);
        toast?.success?.("商品视频生成完成");
      } else if (status === "failed" || status === "timeout") {
        stopPollingCard(card.id);
        card.status = status;
        card.errorMessage = data.error_message || (status === "timeout" ? "视频生成超时" : "视频生成失败");
        genLogs.value.push(`[${card.strategyTitle}] ${status === "timeout" ? "超时" : "失败"}：${card.errorMessage}`);
        toast?.error?.(card.errorMessage);
      } else {
        card.status = status === "done" ? "processing" : status;
      }
    } catch {
      // 单次轮询失败不打断任务。
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

  function removeCard(card) {
    outputCards.value = outputCards.value.filter((item) => item.id !== card.id);
    stopPollingCard(card.id);
  }

  function getVideoModuleName(typeId) {
    return getVideoDemoType(typeId).title || "商品视频";
  }

  onBeforeUnmount(() => {
    runner.cleanup();
  });

  return {
    settings,
    uploadedImages,
    mainImageIndex,
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
    selectedCardsCount,
    loadCreditCosts,
    updateSettings,
    showNotice,
    generateProductVideo,
    createNewTask,
    resetWorkspaceToDraft,
    updateCurrentJobTitle,
    loadHistoryTasks,
    loadGenerationJob,
    toggleCardSelection,
    toggleSelectAllCards,
    downloadSingleVideo,
    batchDownload,
    removeCard,
    getVideoModuleName,
  };
}
