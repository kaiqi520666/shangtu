import { computed, onBeforeUnmount, reactive, ref } from "vue";
import { ratioOptions, resolutionMap, resolveQuality } from "@/constants/generator.js";
import { optimizeFreeImagePrompt } from "@/api/image.js";
import { useCardActions } from "@/composables/useCardActions.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/useGenerationCards.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { useToast } from "@/composables/useToast.js";

function makePromptTitle(prompt) {
  const compact = (prompt || "").trim().replace(/\s+/g, " ");
  if (!compact) return "自由生图";
  return compact.length > 20 ? `${compact.slice(0, 20)}...` : compact;
}

export function useFreeImageGenerator({ onJobCreated } = {}) {
  const toast = useToast();

  const cards = useGenerationCards({
    getLogPrefix: (card) => card.strategyTitle || "自由生图",
    onBatchFinished: createBatchFinishedHandler({
      getGenLogs: () => genLogs,
      toast,
      doneLog: "自由生图任务已结束",
      successText: "自由生图已生成",
      allFailedText: "自由生图生成失败，请稍后重试",
      partialFailedText: (failed) => `部分自由生图生成失败（${failed} 张）`,
    }),
  });

  const {
    outputCards,
    genLogs,
    generating,
    generatedCount,
    jobTotal,
    startPollingCard,
    restoreCard: restoreGenerationCard,
    makeId,
  } = cards;

  const referenceImages = ref([]);
  const mainImageIndex = ref(0);
  const optimizing = ref(false);

  const settings = reactive({
    ratio: "1:1",
    quality: "1K",
    prompt: "",
    platform: "自由生图",
    language: "",
  });

  const runner = useGenerationRunner({
    scenario: "free_image",
    cards,
    toast,
    onJobCreated,
    resetSceneState() {
      referenceImages.value = [];
      mainImageIndex.value = 0;
      settings.prompt = "";
    },
    applyJobData(data) {
      restoreFreeImageJobData(data);
    },
    restoreCard(item) {
      return restoreGenerationCard(item, {
        typeId: item.type_id || "free",
        strategyTitle: item.title || makePromptTitle(item.user_prompt || item.prompt),
        strategyContent: item.user_prompt || item.prompt || "",
        userPrompt: item.user_prompt || item.prompt || "",
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
    enqueueImageBatch,
  } = runner;

  const actions = useCardActions({
    outputCards,
    currentTaskTitle,
    getCardName: (card) => card.strategyTitle || "自由生图",
    toast,
  });

  const {
    zoomCard,
    selectedCards,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleImage,
  } = actions;

  const totalCount = computed(() => 1);
  const hasPrompt = computed(() => settings.prompt.trim().length > 0);
  const hasUploadingReference = computed(() =>
    referenceImages.value.some((image) => image?.uploading),
  );
  const canOptimize = computed(() => hasPrompt.value && !optimizing.value);
  const canGenerate = computed(
    () => hasPrompt.value && !hasUploadingReference.value && !generating.value,
  );
  const selectedRatioOption = computed(
    () => ratioOptions.find((option) => option.value === settings.ratio) || ratioOptions[0],
  );
  const selectedImageLabel = computed(() => {
    const { width, height } = getCardSize();
    return `${settings.quality} / ${selectedRatioOption.value.label} / ${width}x${height}`;
  });

  function restoreFreeImageJobData(data) {
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      if (typeof s.ratio === "string" && resolutionMap[s.ratio]) {
        settings.ratio = s.ratio;
      }
      const desiredQuality = typeof s.quality === "string" ? s.quality : settings.quality;
      settings.quality = resolveQuality(settings.ratio, desiredQuality) || "1K";
      if (typeof s.prompt === "string") {
        settings.prompt = s.prompt;
      }
    }

    if (Array.isArray(data.source_images)) {
      referenceImages.value = data.source_images.map((img) => ({
        ...img,
        previewUrl: img?.url || img?.previewUrl || "",
      }));
      mainImageIndex.value = 0;
    } else {
      referenceImages.value = [];
      mainImageIndex.value = 0;
    }

    if (typeof data.input_text === "string") {
      settings.prompt = data.input_text;
    }
  }

  async function optimizePrompt() {
    const prompt = settings.prompt.trim();
    if (!prompt) {
      toast.info("请先输入提示词");
      return;
    }

    optimizing.value = true;
    try {
      const result = await optimizeFreeImagePrompt(prompt);
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
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "AI优化失败，请稍后重试");
      }
    } finally {
      optimizing.value = false;
    }
  }

  async function generateFreeImage() {
    const prompt = settings.prompt.trim();
    if (!prompt) {
      toast.info("请输入提示词");
      return;
    }
    if (hasUploadingReference.value) {
      toast.info("参考图还在上传中，请稍候");
      return;
    }

    const title = makePromptTitle(prompt);
    const queue = [
      {
        id: "free",
        title,
        prompt,
      },
    ];

    const snapshotPayload = {
      settings: {
        ratio: settings.ratio,
        quality: settings.quality,
        prompt,
      },
      source_images: referenceImages.value.map((img) => ({
        id: img.id,
        url: img.url,
        objectKey: img.objectKey,
        contentType: img.contentType,
        size: img.size,
        previewUrl: img.url || img.previewUrl,
      })),
      input_text: prompt,
      structure: [{ id: "free", title, prompt }],
    };

    const imageUrls = referenceImages.value.map((img) => img.url).filter(Boolean);

    await enqueueImageBatch({
      queue,
      imageUrls,
      ratio: settings.ratio,
      resolution: settings.quality,
      snapshotPayload,
      initialLogs: ["自由生图任务初始化...", "读取提示词与参考图..."],
      repeatLog: "新一张自由生图开始生成",
      buildPrompt: (item) => item.prompt,
      buildUserPrompt: (item) => item.prompt,
      buildSettingsSnapshot: () => ({
        scenario: "free_image",
        platform: "自由生图",
        language: "",
        ratio: settings.ratio,
        quality: settings.quality,
      }),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot }) {
        return reactive({
          id: makeId(),
          taskId: "",
          typeId: item.id,
          dataUrl: "",
          resultUrl: "",
          selected: true,
          status: "pending",
          strategyTitle: item.title,
          strategyContent: item.prompt,
          errorMessage: "",
          sortOrder,
          batchRunId,
          creditRefunded: false,
          userPrompt: item.prompt,
          settingsSnapshot,
        });
      },
      getCreateLog: (item) => `正在生成 [${item.title}]...`,
      getFailLogName: (item) => item.title,
      allFailedMessage: "自由生图任务创建失败，请稍后重试",
    });
  }

  function getCardSize() {
    const effectiveQuality = resolveQuality(settings.ratio, settings.quality) || settings.quality;
    const dims = resolutionMap[settings.ratio]?.[effectiveQuality];
    if (!dims) {
      throw new Error(`不支持的尺寸组合：${settings.ratio} / ${settings.quality}`);
    }
    if (effectiveQuality !== settings.quality) {
      settings.quality = effectiveQuality;
    }
    const [width, height] = dims;
    return { width, height };
  }

  function getModuleName() {
    return "自由生图";
  }

  function showNotice(message) {
    toast.info(message);
  }

  onBeforeUnmount(() => {
    runner.cleanup();
  });

  return {
    referenceImages,
    mainImageIndex,
    optimizing,
    settings,
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    generating,
    generatedCount,
    jobTotal,
    genLogs,
    outputCards,
    zoomCard,
    selectedCards,
    selectedCardsCount,
    totalCount,
    canOptimize,
    canGenerate,
    selectedImageLabel,
    showNotice,
    optimizePrompt,
    generateFreeImage,
    getModuleName,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleImage,
    createNewTask,
    resetWorkspaceToDraft,
    updateCurrentJobTitle,
    loadHistoryTasks,
    loadGenerationJob,
    startPollingCard,
  };
}
