import { computed, onBeforeUnmount, reactive, ref } from "vue";
import {
  deleteVideoTask,
  generateVideo,
  getVideoCreditCosts,
  getVideoDownloadUrl,
  getVideoTask,
  optimizeFreeVideoPrompt,
} from "@/api/video.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/generator/useGenerationCards.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useMediaBatchRunner } from "@/composables/generator/batch/useMediaBatchRunner.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import { multiplyCreditCosts } from "@/utils/creditPricing.js";
import {
  cloneGenerationSettingsSnapshot,
  createGenerationSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";
import {
  defaultVideoCreditCosts,
  getVideoCreditCost,
} from "@/constants/product-video.js";
import { makeFreeVideoTitle } from "@/constants/free-video.js";

const VIDEO_POLL_INTERVAL_MS = 3000;

function serializeImages(images) {
  return images.map((img) => ({
    id: img.id,
    url: img.url,
    objectKey: img.objectKey,
    contentType: img.contentType,
    size: img.size,
    previewUrl: img.url || img.previewUrl,
  }));
}

function serializeMedia(items) {
  return items.map((item) => ({
    id: item.id,
    url: item.url,
    objectKey: item.objectKey,
    contentType: item.contentType,
    size: item.size,
    name: item.name || "",
    previewUrl: item.url || item.previewUrl,
    source: item.source || "",
    assetTaskId: item.assetTaskId || "",
  }));
}

export function useFreeVideoGenerator({ confirm, onJobCreated } = {}) {
  const toast = useToast();
  const uploadedImages = ref([]);
  const uploadedVideos = ref([]);
  const uploadedAudios = ref([]);
  const mainImageIndex = ref(0);
  const optimizing = ref(false);
  const creditCosts = ref({ ...defaultVideoCreditCosts });
  const settings = reactive({
    prompt: "",
    duration: 8,
    resolution: "720p",
    aspectRatio: "9:16",
    generateAudio: false,
    enableWebSearch: false,
  });

  const cards = useGenerationCards({
    getTask: getVideoTask,
    pollIntervalMs: VIDEO_POLL_INTERVAL_MS,
    mediaLabel: "视频",
    preloadResult: false,
    getLogPrefix: (card) => card.strategyTitle || "自由生视频",
    onCardDone: (card) => {
      card.progress = 100;
    },
    onBatchFinished: createBatchFinishedHandler({
      genLogs: null,
      toast,
      doneLog: "自由生视频任务已结束",
      successText: "自由生视频生成完成",
      allFailedText: "自由生视频生成失败，请稍后重试",
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

  const runner = useMediaBatchRunner({
    scenario: "free_video",
    cards,
    toast,
    onJobCreated,
    mediaUnit: "个",
    resetSceneState() {
      uploadedImages.value = [];
      uploadedVideos.value = [];
      uploadedAudios.value = [];
      mainImageIndex.value = 0;
      settings.prompt = "";
      settings.duration = 8;
      settings.resolution = "720p";
      settings.aspectRatio = "9:16";
      settings.generateAudio = false;
      settings.enableWebSearch = false;
    },
    applyJobData(data) {
      restoreFreeVideoJobData(data);
    },
    restoreCard(item) {
      const prompt = item.prompt_snapshot?.user || item.prompt || "";
      return createCard({
        taskId: item.task_id,
        title: item.title || makeFreeVideoTitle(prompt),
        settingsSnapshot: item.settings_snapshot || null,
        creditCost: item.credit_cost || 0,
        status: item.status || "pending",
        resultUrl: item.result_url || "",
        errorMessage: item.error_message || "",
        progress: item.progress || 0,
        sortOrder: item.sort_order || 0,
        strategyContent: prompt,
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
    getCardName: (card) => card.strategyTitle || "自由生视频",
    getDownloadUrl: (card) => getVideoDownloadUrl(card.taskId),
    mediaLabel: "视频",
    mediaUnit: "个",
    archiveName: "自由生视频",
    toast,
  });

  const {
    downloading,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleMedia: downloadSingleVideo,
  } = actions;

  const hasPrompt = computed(() => settings.prompt.trim().length > 0);
  const hasUploadingImages = computed(() => uploadedImages.value.some((img) => img?.uploading));
  const hasUploadingVideos = computed(() => uploadedVideos.value.some((item) => item?.uploading));
  const hasUploadingAudios = computed(() => uploadedAudios.value.some((item) => item?.uploading));
  const hasRunningTasks = computed(() => runningCount.value > 0 || creatingBatch.value || generating.value);
  const estimatedCredits = computed(() =>
    getVideoCreditCost({
      resolution: settings.resolution,
      duration: settings.duration,
      costs: creditCosts.value,
    }),
  );
  const canOptimize = computed(() => hasPrompt.value && !optimizing.value);
  const canGenerate = computed(() => {
    if (!hasPrompt.value || hasUploadingImages.value || hasUploadingVideos.value || hasUploadingAudios.value || creatingBatch.value) return false;
    const imageCount = uploadedImages.value.filter((img) => img?.url).length;
    const videoCount = uploadedVideos.value.filter((item) => item?.url).length;
    const audioCount = uploadedAudios.value.filter((item) => item?.url).length;
    return imageCount <= 9 && videoCount <= 3 && audioCount <= 3;
  });
  const selectedVideoLabel = computed(
    () => `${settings.resolution} / ${settings.aspectRatio} / ${settings.duration}秒`,
  );

  async function loadCreditCosts() {
    try {
      const result = await getVideoCreditCosts();
      if (result.code === 0 && result.data?.costs) {
        creditCosts.value = {
          ...defaultVideoCreditCosts,
          ...multiplyCreditCosts(result.data.costs, result.data.consumption_multiplier),
        };
      }
    } catch {
      toast.info("视频扣费配置读取失败，已使用默认配置");
    }
  }

  function updateSettings(nextSettings) {
    Object.assign(settings, nextSettings);
  }

  function restoreFreeVideoJobData(data) {
    const sourceSettings = data.settings || {};
    const scene = getSnapshotScene(sourceSettings);
    if (typeof scene.prompt === "string") settings.prompt = scene.prompt;
    if (typeof scene.duration === "number") settings.duration = scene.duration;
    if (typeof scene.resolution === "string") settings.resolution = scene.resolution;
    if (typeof scene.aspectRatio === "string") settings.aspectRatio = scene.aspectRatio;
    settings.generateAudio = Boolean(scene.generateAudio);
    settings.enableWebSearch = Boolean(scene.enableWebSearch);
    if (typeof data.input_text === "string") settings.prompt = data.input_text;

    if (Array.isArray(data.source_images)) {
      uploadedImages.value = data.source_images.map((img) => ({
        ...img,
        previewUrl: img?.url || img?.previewUrl || "",
      }));
    } else {
      uploadedImages.value = [];
    }
    if (Array.isArray(data.source_videos)) {
      uploadedVideos.value = data.source_videos.map((item) => ({
        ...item,
        previewUrl: item?.previewUrl || item?.url || "",
      }));
    } else {
      uploadedVideos.value = [];
    }
    if (Array.isArray(data.source_audios)) {
      uploadedAudios.value = data.source_audios.map((item) => ({
        ...item,
        previewUrl: item?.previewUrl || item?.url || "",
      }));
    } else {
      uploadedAudios.value = [];
    }
    mainImageIndex.value = 0;
  }

  function validateInputs() {
    const prompt = settings.prompt.trim();
    if (!prompt) return "请输入视频提示词";
    if (hasUploadingImages.value) return "素材还在上传中，请稍等";
    if (hasUploadingVideos.value) return "参考视频还在上传中，请稍等";
    if (hasUploadingAudios.value) return "参考音频还在上传中，请稍等";
    const imageCount = uploadedImages.value.filter((img) => img?.url).length;
    const videoCount = uploadedVideos.value.filter((item) => item?.url).length;
    const audioCount = uploadedAudios.value.filter((item) => item?.url).length;
    if (imageCount > 9) return "参考图最多只能上传 9 张";
    if (videoCount > 3) return "参考视频最多只能上传 3 条";
    if (audioCount > 3) return "参考音频最多只能上传 3 条";
    return "";
  }

  async function optimizePrompt() {
    const prompt = settings.prompt.trim();
    if (!prompt) {
      toast.info("请先输入视频提示词");
      return;
    }
    optimizing.value = true;
    try {
      const result = await optimizeFreeVideoPrompt(prompt);
      if (result.code !== 0) {
        toast.error(result.message || "AI优化失败");
        return;
      }
      const optimized = result.data?.prompt?.trim();
      if (!optimized) {
        toast.error("AI未返回有效提示词");
        return;
      }
      settings.prompt = optimized;
      toast.success("AI优化已覆盖提示词");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "AI优化失败，请稍后重试"));
    } finally {
      optimizing.value = false;
    }
  }

  function createSettingsSnapshot(prompt) {
    return createGenerationSettingsSnapshot({
      scenario: "free_video",
      mediaType: "video",
      platform: "自由生视频",
      language: "",
      ratio: settings.aspectRatio,
      quality: settings.resolution,
      scene: {
        prompt,
        duration: settings.duration,
        resolution: settings.resolution,
        aspectRatio: settings.aspectRatio,
        generateAudio: settings.generateAudio,
        enableWebSearch: settings.enableWebSearch,
      },
    });
  }

  function createCard({
    taskId = "",
    title,
    settingsSnapshot,
    creditCost = 0,
    status = "pending",
    resultUrl = "",
    errorMessage = "",
    progress = 0,
    sortOrder = outputCards.value.length,
    batchRunId = "",
    strategyContent = "",
  }) {
    const scene = getSnapshotScene(settingsSnapshot);
    const content = strategyContent || scene.prompt || "";
    const card = cards.createCard({
      typeId: "free_video",
      strategyTitle: title || makeFreeVideoTitle(content),
      strategyContent: content,
      sortOrder,
      batchRunId,
      userPrompt: content,
      settingsSnapshot,
    });
    card.taskId = taskId;
    card.dataUrl = resultUrl;
    card.resultUrl = resultUrl;
    card.status = status;
    card.errorMessage = errorMessage;
    card.creditCost = creditCost;
    card.progress = progress;
    return card;
  }

  async function generateFreeVideo() {
    if (generating.value || creatingBatch.value) {
      toast.info("当前视频任务还在生成中");
      return;
    }
    const validationMessage = validateInputs();
    if (validationMessage) {
      toast.info(validationMessage);
      return;
    }

    const prompt = settings.prompt.trim();
    const title = makeFreeVideoTitle(prompt);
    const settingsSnapshot = createSettingsSnapshot(prompt);
    const imageUrls = uploadedImages.value.map((img) => img?.url).filter(Boolean);
    const videoUrls = uploadedVideos.value.map((item) => item?.url).filter(Boolean);
    const audioUrls = uploadedAudios.value.map((item) => item?.url).filter(Boolean);
    const queue = [{ id: "free_video", title, prompt }];

    await enqueueMediaBatch({
      queue,
      snapshotPayload: {
        settings: settingsSnapshot,
        source_images: serializeImages(uploadedImages.value),
        source_videos: serializeMedia(uploadedVideos.value),
        source_audios: serializeMedia(uploadedAudios.value),
        input_text: prompt,
        structure: [{ id: "free_video", title, prompt }],
      },
      initialLogs: ["自由生视频任务初始化...", "读取视频提示词与素材..."],
      repeatLog: "新一个自由生视频开始生成",
      buildSettingsSnapshot: () => cloneGenerationSettingsSnapshot(settingsSnapshot),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot: snapshot }) {
        return createCard({
          title: item.title,
          settingsSnapshot: snapshot,
          strategyContent: item.prompt,
          sortOrder,
          batchRunId,
        });
      },
      createTask({ item, card, settingsSnapshot: snapshot, jobId }) {
        return generateVideo({
          scenario: "free_video",
          type_id: item.id,
          title: item.title,
          input_mode: "multimodal_reference",
          image_urls: imageUrls,
          video_urls: videoUrls,
          audio_urls: audioUrls,
          user_prompt: item.prompt,
          duration: settings.duration,
          resolution: settings.resolution,
          aspect_ratio: settings.aspectRatio,
          generate_audio: settings.generateAudio,
          enable_web_search: settings.enableWebSearch,
          settings_snapshot: snapshot,
          sort_order: card.sortOrder,
          job_id: jobId,
        });
      },
      getCreateLog: (item) => `正在生成 [${item.title}]...`,
      getFailLogName: (item) => item.title,
      allFailedMessage: "自由生视频任务创建失败，请稍后重试",
      saveErrorMessage: "保存自由生视频配置失败",
      taskIdMissingMessage: "视频任务创建失败：后端未返回任务 ID",
      preferCreateErrorAsToast: true,
    });
  }

  async function removeCard(card) {
    if (!card?.taskId) {
      outputCards.value = outputCards.value.filter((item) => item.id !== card?.id);
      return;
    }

    const ok = await confirm?.open?.({
      title: "删除视频",
      message: "确定删除这个视频吗？视频不会立即从存储中物理删除。",
      confirmText: "删除",
      cancelText: "取消",
      tone: "danger",
    });
    if (ok === false) return;

    try {
      const result = await deleteVideoTask(card.taskId);
      if (result.code !== 0) {
        toast.error(result.message || "删除失败");
        return;
      }
      outputCards.value = outputCards.value.filter((item) => item.id !== card.id);
      stopPollingCard(card.id);
      toast.success("视频已删除");
    } catch {
      toast.error("删除失败，请稍后重试");
    }
  }

  function showNotice(message) {
    toast.info(message);
  }

  function getModuleName() {
    return "自由生视频";
  }

  onBeforeUnmount(() => {
    runner.cleanup();
  });

  return {
    settings,
    uploadedImages,
    uploadedVideos,
    uploadedAudios,
    mainImageIndex,
    optimizing,
    creditCosts,
    estimatedCredits,
    canOptimize,
    canGenerate,
    hasRunningTasks,
    selectedVideoLabel,
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
    loadCreditCosts,
    updateSettings,
    showNotice,
    optimizePrompt,
    generateFreeVideo,
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
    getModuleName,
  };
}
