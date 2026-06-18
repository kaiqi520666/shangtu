import { onBeforeUnmount, reactive, ref } from "vue";
import { deleteVideoTask, generateVideo, getVideoCreditCosts, getVideoDownloadUrl, getVideoTask } from "@/api/video.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/useGenerationCards.js";
import { useAiSellingPointsWriter } from "@/composables/useAiSellingPointsWriter.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { buildVideoAnalyzeImages } from "@/utils/analyzeImages.js";
import {
  createVideoSettingsSnapshot,
  getSnapshotScene,
  getSnapshotValue,
} from "@/utils/generationSnapshots.js";
import {
  defaultVideoCreditCosts,
  getVideoDemoType,
  videoDemoTypes,
  videoLanguageOptions,
  videoMarketOptions,
  videoSizeOptions,
} from "@/constants/productVideo.js";

const VIDEO_POLL_INTERVAL_MS = 3000;

function getOptionLabel(options, value) {
  return options.find((item) => item.value === value)?.label || value;
}

function getSelectedSize(sizePreset) {
  return videoSizeOptions.find((item) => item.value === sizePreset) || videoSizeOptions[0];
}

function buildSettingsSnapshot(settings) {
  const selectedType = getVideoDemoType(settings.videoType);
  const selectedSize = getSelectedSize(settings.sizePreset);
  return createVideoSettingsSnapshot({
    videoType: settings.videoType,
    title: selectedType.title,
    inputMode: selectedType.inputMode,
    market: settings.market,
    marketLabel: getOptionLabel(videoMarketOptions, settings.market),
    language: settings.language,
    languageLabel: getOptionLabel(videoLanguageOptions, settings.language),
    sizePreset: settings.sizePreset,
    aspectRatio: selectedSize.aspectRatio,
    duration: settings.duration,
    resolution: settings.resolution,
    productInput: settings.productInput,
  });
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
  const cards = useGenerationCards({
    getTask: getVideoTask,
    pollIntervalMs: VIDEO_POLL_INTERVAL_MS,
    mediaLabel: "视频",
    preloadResult: false,
    getLogPrefix: (card) => card.strategyTitle || getVideoModuleName(card.typeId),
    onCardDone: (card) => {
      card.progress = 100;
    },
    onBatchFinished: createBatchFinishedHandler({
      genLogs: null,
      toast,
      doneLog: "商品视频任务已结束",
      successText: "商品视频生成完成",
      allFailedText: "商品视频生成失败，请稍后重试",
      partialFailedText: (failed) => `${failed} 个视频生成失败，其余已完成`,
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

  const { aiLoading, generateSellingPointsWithAI } = useAiSellingPointsWriter({
    toast,
    buildImages: () => {
      const selectedType = getVideoDemoType(settings.videoType);
      return buildVideoAnalyzeImages(selectedType.inputMode, uploadedImages.value);
    },
    getUploadedImages: () => uploadedImages.value,
    getAnalyzePayload: () => {
      const selectedType = getVideoDemoType(settings.videoType);
      return {
        platform: settings.market,
        scenario: "product_video",
        type_id: selectedType.typeId,
      };
    },
    validate: () => {
      const selectedType = getVideoDemoType(settings.videoType);
      const imageCount = uploadedImages.value.filter((item) => item?.url).length;
      return getRequiredImageMessage(selectedType.inputMode, imageCount);
    },
    uploadingMessage: "素材还在上传中，请稍候",
  });

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

  const runner = useGenerationRunner({
    scenario: "product_video",
    cards,
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
    createNewTask,
    resetWorkspaceToDraft,
    loadHistoryTasks,
    loadGenerationJob,
    enqueueMediaBatch,
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
    batchRunId = "",
  }) {
    const scene = getSnapshotScene(settingsSnapshot);
    const productInput = scene.productInput ?? settingsSnapshot?.product_input ?? "";
    const card = cards.createCard({
      typeId,
      strategyTitle: title || "商品视频",
      strategyContent: productInput,
      sortOrder,
      batchRunId,
      userPrompt: productInput,
      settingsSnapshot,
    });
    card.taskId = taskId || "";
    card.dataUrl = resultUrl;
    card.resultUrl = resultUrl;
    card.status = status;
    card.errorMessage = errorMessage;
    card.creditCost = creditCost;
    card.progress = progress;
    return card;
  }

  function restoreVideoJobData(data) {
    const s = data.settings || {};
    const scene = getSnapshotScene(s);
    const videoType = scene.videoType ?? s.type_id;
    const inputMode = scene.inputMode ?? s.input_mode;
    const market = scene.market ?? s.market ?? getSnapshotValue(s, "platform");
    const language = scene.language ?? getSnapshotValue(s, "language");
    const sizePreset = scene.sizePreset ?? s.size_preset;
    const duration = scene.duration ?? s.duration;
    const resolution = scene.resolution ?? s.resolution ?? getSnapshotValue(s, "quality");
    const productInput = scene.productInput ?? s.product_input;
    if (typeof videoType === "string") {
      settings.videoType = videoType;
      settings.inputMode = getVideoDemoType(videoType).inputMode;
    }
    if (typeof inputMode === "string") settings.inputMode = inputMode;
    if (typeof market === "string") settings.market = market;
    if (typeof language === "string") settings.language = language;
    if (typeof sizePreset === "string") settings.sizePreset = sizePreset;
    if (typeof duration === "number") settings.duration = duration;
    if (typeof resolution === "string") settings.resolution = resolution;
    settings.productInput = data.input_text || productInput || "";
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
    const queue = [{ ...selectedType }];

    await enqueueMediaBatch({
      queue,
      snapshotPayload: {
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
      },
      initialLogs: [`[${selectedType.title}] 创建视频任务`],
      repeatLog: `[${selectedType.title}] 创建视频任务`,
      buildSettingsSnapshot: () => settingsSnapshot,
      createCard({ item, sortOrder, batchRunId, settingsSnapshot: snapshot }) {
        return createCard({
          typeId: item.typeId,
          title: item.title,
          settingsSnapshot: snapshot,
          sortOrder,
          batchRunId,
        });
      },
      createTask({ item, card, settingsSnapshot: snapshot, jobId }) {
        return generateVideo({
          type_id: item.typeId,
          title: item.title,
          input_mode: item.inputMode,
          image_urls: imageUrls,
          user_prompt: settings.productInput,
          duration: settings.duration,
          resolution: settings.resolution,
          aspect_ratio: getSnapshotScene(snapshot).aspectRatio || snapshot.aspect_ratio || snapshot.ratio,
          settings_snapshot: snapshot,
          sort_order: card.sortOrder,
          job_id: jobId,
        });
      },
      getCreateLog: (item) => `[${item.title}] 已进入队列`,
      getFailLogName: (item) => item.title,
      allFailedMessage: "视频任务创建失败，请稍后重试",
      saveErrorMessage: "保存视频任务配置失败",
      taskIdMissingMessage: "视频任务创建失败：后端未返回任务 ID",
      insertCards: "after-success",
      preferCreateErrorAsToast: true,
    });
  }

  async function removeCard(card) {
    if (!card?.taskId) {
      outputCards.value = outputCards.value.filter((item) => item.id !== card?.id);
      return;
    }

    try {
      const result = await deleteVideoTask(card.taskId);
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
    aiLoading,
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
    generateSellingPointsWithAI,
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
