import { computed, onBeforeUnmount, reactive, ref } from "vue";
import {
  deleteVideoTask,
  generateVideo,
  generateVideoStrategy,
  getVideoCreditCosts,
  getVideoDownloadUrl,
  getVideoTask,
} from "@/api/video.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/generator/useGenerationCards.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useMediaBatchRunner } from "@/composables/generator/batch/useMediaBatchRunner.js";
import { useGenerationStrategyFlow } from "@/composables/generator/strategy/useGenerationStrategyFlow.js";
import { buildVideoAnalyzeImages } from "@/utils/analyzeImages.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import {
  createVideoSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";
import {
  defaultVideoCreditCosts,
  getVideoCreditCost,
  getVideoDemoType,
  videoDemoTypes,
  videoLanguageOptions,
  videoMarketOptions,
  videoSizeOptions,
} from "@/constants/product-video.js";

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

function attachVideoStrategyBrief(snapshot, brief) {
  return {
    ...snapshot,
    scene: {
      ...(snapshot.scene || {}),
      strategyBrief: brief,
    },
  };
}

function getRequiredImageMessage(inputMode, count) {
  if (inputMode === "image_to_video" && count !== 1) return "请上传 1 张首帧图";
  if (inputMode === "reference_to_video" && (count < 1 || count > 9)) {
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
  const selectedType = computed(() => getVideoDemoType(settings.videoType));
  const selectedSize = computed(() => getSelectedSize(settings.sizePreset));
  const estimatedCredits = computed(() =>
    getVideoCreditCost({
      resolution: settings.resolution,
      duration: settings.duration,
      costs: creditCosts.value,
    }),
  );
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

  const strategyFlow = useGenerationStrategyFlow({
    buildInputSnapshot: buildVideoStrategySnapshot,
  });

  const {
    workflowStep,
    strategyBrief,
    strategyItems: videoStrategyItems,
    strategySnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    startStrategyLoading,
    setStrategyResult,
    resetStrategy,
    setStrategyStep,
    updateStrategyItem,
    backToConfig,
  } = strategyFlow;

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

  const runner = useMediaBatchRunner({
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
      resetStrategy("config");
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
        strategyContent: item.prompt_snapshot?.user || "",
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

  const hasRunningTasks = computed(() => runningCount.value > 0 || creatingBatch.value || generating.value);
  const canGenerateStrategy = computed(() => {
    const images = uploadedImages.value.filter((item) => item?.url);
    return (
      !getRequiredImageMessage(selectedType.value.inputMode, images.length) &&
      !uploadedImages.value.some((item) => item?.uploading) &&
      !strategyLoading.value &&
      !creatingBatch.value &&
      !hasRunningTasks.value
    );
  });
  const strategyMetaText = computed(
    () =>
      `${selectedType.value.title} / ${getOptionLabel(videoMarketOptions, settings.market)} / ${getOptionLabel(videoLanguageOptions, settings.language)} / ${settings.duration}秒 / ${selectedSize.value.aspectRatio} / ${settings.resolution}`,
  );

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
    strategyContent = "",
  }) {
    const scene = getSnapshotScene(settingsSnapshot);
    const productInput = typeof scene.productInput === "string" ? scene.productInput : "";
    const content = strategyContent || productInput;
    const card = cards.createCard({
      typeId,
      strategyTitle: title || "商品视频",
      strategyContent: content,
      sortOrder,
      batchRunId,
      userPrompt: content,
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
    const videoType = scene.videoType;
    const inputMode = scene.inputMode;
    const market = scene.market || s.platform;
    const language = scene.language || s.language;
    const sizePreset = scene.sizePreset;
    const duration = scene.duration;
    const resolution = scene.resolution || s.quality;
    const productInput = scene.productInput;
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

    if (Array.isArray(data.structure) && data.structure.length > 0) {
      setStrategyResult({
        brief: getSnapshotScene(data.settings || {}).strategyBrief || "",
        items: normalizeVideoStrategyItems(data.structure),
        snapshot: buildVideoStrategySnapshot(),
        step: "strategy-review",
      });
    } else {
      resetStrategy("config");
    }
  }

  async function triggerStrategyGeneration() {
    const imageUrls = uploadedImages.value.map((item) => item?.url).filter(Boolean);
    const requirementMessage = getRequiredImageMessage(selectedType.value.inputMode, imageUrls.length);
    if (requirementMessage) {
      toast?.info?.(requirementMessage);
      return;
    }
    if (uploadedImages.value.some((item) => item?.uploading)) {
      toast?.info?.("素材还在上传中，请稍等");
      return;
    }
    if (hasRunningTasks.value) {
      toast?.info?.("当前视频任务还在生成中，请稍后再生成视频提示词");
      return;
    }

    const inputSnapshot = buildVideoStrategySnapshot();
    startStrategyLoading({ snapshot: inputSnapshot });

    try {
      const result = await generateVideoStrategy({
        type_id: selectedType.value.typeId,
        name: selectedType.value.title,
        input_mode: selectedType.value.inputMode,
        images: inputSnapshot.images,
        market: settings.market,
        language: settings.language,
        duration: settings.duration,
        aspect_ratio: selectedSize.value.aspectRatio,
        product_input: settings.productInput,
      });

      if (result.code !== 0) {
        toast?.error?.(result.message || "视频提示词生成失败，请稍后重试");
        setStrategyStep("config");
        return;
      }

      const items = Array.isArray(result.data?.items) ? result.data.items : [];
      if (items.length === 0) {
        toast?.error?.("AI 未返回有效视频提示词");
        setStrategyStep("config");
        return;
      }

      const normalizedItems = normalizeVideoStrategyItems(items);
      setStrategyResult({
        brief: result.data?.brief || `已生成「${selectedType.value.title}」视频提示词。`,
        items: normalizedItems,
        snapshot: inputSnapshot,
      });
      toast?.success?.("视频提示词已生成，可编辑后继续出片");
    } catch (error) {
      toast?.error?.(getApiErrorMessage(error, "视频提示词生成失败，请稍后重试"));
      setStrategyStep("config");
    }
  }

  async function confirmStrategyAndGenerate() {
    if (!canGenerateWithStrategy.value) {
      toast?.info?.(strategyDirty.value ? "配置已变化，请重新生成视频提示词" : "请先生成视频提示词");
      return;
    }
    await generateProductVideo();
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
    const videoScript = getConfirmedVideoScript();
    if (!videoScript) {
      toast?.info?.("请先生成并确认视频提示词");
      return;
    }

    const settingsSnapshot = attachVideoStrategyBrief(buildSettingsSnapshot(settings), strategyBrief.value);
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
        structure: videoStrategyItems.value,
      },
      initialLogs: [`[${selectedType.title}] 创建视频任务`, "读取视频提示词与平台规范..."],
      repeatLog: `[${selectedType.title}] 创建视频任务`,
      buildSettingsSnapshot: () => settingsSnapshot,
      createCard({ item, sortOrder, batchRunId, settingsSnapshot: snapshot }) {
        return createCard({
          typeId: item.typeId,
          title: item.title,
          settingsSnapshot: snapshot,
          strategyContent: videoScript,
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
          user_prompt: videoScript,
          duration: settings.duration,
          resolution: settings.resolution,
          aspect_ratio: getSnapshotScene(snapshot).aspectRatio || snapshot.ratio,
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

  function buildVideoStrategySnapshot() {
    return {
      scenario: "product_video",
      type_id: selectedType.value.typeId,
      input_mode: selectedType.value.inputMode,
      market: settings.market,
      language: settings.language,
      duration: settings.duration,
      aspect_ratio: selectedSize.value.aspectRatio,
      product_input: settings.productInput,
      images: buildVideoAnalyzeImages(selectedType.value.inputMode, uploadedImages.value),
    };
  }

  function normalizeVideoStrategyItems(items) {
    const source = Array.isArray(items) ? items : [];
    return source.slice(0, 1).map((item) => {
      const type = getVideoDemoType(item.id || settings.videoType);
      return {
        id: item.id || type.typeId,
        name: item.name || type.title,
        content: item.content || "",
      };
    });
  }

  function updateVideoScript(content) {
    updateStrategyItem(0, { content });
  }

  function getConfirmedVideoScript() {
    return (videoStrategyItems.value[0]?.content || "").trim();
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
    workflowStep,
    strategyBrief,
    strategySnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    videoStrategyItems,
    estimatedCredits,
    canGenerateStrategy,
    strategyMetaText,
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
    triggerStrategyGeneration,
    confirmStrategyAndGenerate,
    updateVideoScript,
    backToConfig,
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
