import { computed, onBeforeUnmount, reactive, ref } from "vue";
import {
  createDefaultGenerationSettings,
  formatImageLabel,
  resolutionMap,
  resolveQuality,
} from "@/constants/generator.js";
import { suiteStructureDefaults } from "@/constants/productSuite.js";
import { useToast } from "@/composables/useToast.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/useGenerationCards.js";
import { useAiSellingPointsWriter } from "@/composables/useAiSellingPointsWriter.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { useGenerationStrategyFlow } from "@/composables/useGenerationStrategyFlow.js";
import { buildProductAnalyzeImages, hasUploadingImages } from "@/utils/analyzeImages.js";
import {
  cloneGenerationSettingsSnapshot,
  createGenerationSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";
import { generateProductSuiteStrategy } from "@/api/image.js";

function createDefaultSuiteStructure() {
  return suiteStructureDefaults.map((item) => ({
    ...item,
    enabled: true,
    count: item.defaultCount,
  }));
}

function cloneUploadedImages(images) {
  return images.map((img) => ({
    id: img.id,
    url: img.url,
    objectKey: img.objectKey,
    contentType: img.contentType,
    size: img.size,
    previewUrl: img.url || img.previewUrl,
  }));
}

export function useProductSuiteGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const genLogs = ref([]);

  const cards = useGenerationCards({
    genLogs,
    getLogPrefix: (card) => card.strategyTitle || card.typeId || "",
    onBatchFinished: createBatchFinishedHandler({
      genLogs,
      toast,
      doneLog: "全部商品套图任务已结束",
      successText: "商品套图已全部生成",
      allFailedText: "套图生成失败，请稍后重试",
      partialFailedText: (failed) => `部分套图生成失败（${failed} 张）`,
    }),
  });

  const {
    outputCards,
    creatingBatch,
    hasRunningTasks,
    generating,
    generatedCount,
    runningCount,
    failedCount,
    jobTotal,
    startPollingCard,
    createCard: createGenerationCard,
    restoreCard: restoreGenerationCard,
  } = cards;

  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);
  const settings = reactive(createDefaultGenerationSettings());
  const suiteStructure = ref(createDefaultSuiteStructure());

  const strategyFlow = useGenerationStrategyFlow({
    buildInputSnapshot: buildSuiteStrategySnapshot,
  });

  const {
    workflowStep,
    strategyBrief,
    strategyItems: suiteStrategyItems,
    strategySnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    startStrategyLoading,
    setStrategyResult,
    resetStrategy,
    setStrategyStep,
    updateStrategyItem: updateSuiteStrategyItem,
    reorderStrategyItems: reorderSuiteStrategyItems,
    removeStrategyItem: removeSuiteStrategyItem,
    backToConfig,
  } = strategyFlow;

  const { aiLoading, generateSellingPointsWithAI } = useAiSellingPointsWriter({
    toast,
    buildImages: () => buildProductAnalyzeImages(uploadedImages.value, mainImageIndex.value),
    getUploadedImages: () => uploadedImages.value,
    getAnalyzePayload: () => ({
      platform: settings.platform,
      scenario: "product_suite",
    }),
  });

  const runner = useGenerationRunner({
    scenario: "product_suite",
    cards,
    toast,
    onJobCreated,
    resetSceneState() {
      uploadedImages.value = [];
      mainImageIndex.value = 0;
      settings.productInput = "";
      suiteStructure.value = createDefaultSuiteStructure();
      resetStrategy("config");
    },
    applyJobData(data) {
      restoreSuiteJobData(data);
    },
    restoreCard(item) {
      const strategyItem = findSuiteStrategyItem(item.type_id);
      return restoreGenerationCard(item, {
        strategyTitle: item.title || strategyItem.title || getStructureName(item.type_id),
        strategyContent: strategyItem.content || strategyItem.strategy || getStructureStrategy(item.type_id),
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
    getCardName: (card) => card.strategyTitle || getStructureName(card.typeId),
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

  const configuredTotalCount = computed(() =>
    suiteStructure.value.reduce((sum, item) => {
      if (!item.enabled) return sum;
      return sum + item.count;
    }, 0),
  );
  const strategyTotalCount = computed(() =>
    suiteStrategyItems.value.reduce((sum, item) => sum + Math.max(0, Number(item.count) || 0), 0),
  );
  const totalCount = computed(() => strategyTotalCount.value || configuredTotalCount.value);
  const hasGenerationSource = computed(
    () => uploadedImages.value.length > 0 && settings.productInput.trim().length > 0,
  );
  const canGenerateStrategy = computed(
    () =>
      hasGenerationSource.value &&
      configuredTotalCount.value > 0 &&
      !strategyLoading.value &&
      !creatingBatch.value &&
      !hasRunningTasks.value,
  );
  const selectedImageLabel = computed(() => {
    syncQualityForRatio();
    return formatImageLabel({ ratio: settings.ratio, quality: settings.quality });
  });

  function restoreSuiteJobData(data) {
    let restoredStrategyBrief = "";
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      const scene = getSnapshotScene(s);
      const { platform, language, ratio, quality } = s;
      const { structureConfig, strategyBrief: nextStrategyBrief } = scene;
      restoredStrategyBrief = typeof nextStrategyBrief === "string" ? nextStrategyBrief : "";
      if (typeof platform === "string") settings.platform = platform;
      if (typeof language === "string") settings.language = language;
      if (typeof ratio === "string" && resolutionMap[ratio]) {
        settings.ratio = ratio;
      }
      const desiredQuality = typeof quality === "string" ? quality : settings.quality;
      settings.quality = resolveQuality(settings.ratio, desiredQuality) || "1K";
      if (Array.isArray(structureConfig) && structureConfig.length > 0) {
        suiteStructure.value = structureConfig;
      }
    }

    if (Array.isArray(data.source_images)) {
      uploadedImages.value = data.source_images.map((img) => ({
        ...img,
        previewUrl: img?.url || img?.previewUrl || "",
      }));
      mainImageIndex.value = 0;
    } else {
      uploadedImages.value = [];
      mainImageIndex.value = 0;
    }

    settings.productInput = data.input_text || "";
    if (Array.isArray(data.structure) && data.structure.length > 0) {
      setStrategyResult({
        brief: restoredStrategyBrief,
        items: normalizeSuiteStrategyItems(data.structure),
        snapshot: buildSuiteStrategySnapshot(),
        step: "result",
      });
    } else {
      resetStrategy("config");
    }
  }

  async function triggerStrategyGeneration() {
    const mainImg = uploadedImages.value[mainImageIndex.value];
    const inputSnapshot = buildSuiteStrategySnapshot();
    if (hasRunningTasks.value) {
      toast.info("当前任务正在生成中，请稍后再生成套图策略");
      return;
    }
    if (creatingBatch.value) {
      toast.info("正在创建图片任务，请稍候");
      return;
    }
    if (!hasGenerationSource.value) {
      toast.info("请先上传商品图片并填写商品卖点与要求");
      return;
    }
    if (!mainImg || !mainImg.url) {
      toast.info("主图还未上传完成，请稍候再试");
      return;
    }
    if (hasUploadingImages(uploadedImages.value)) {
      toast.info("商品图还在上传中，请稍候");
      return;
    }
    if (configuredTotalCount.value === 0) {
      toast.info("请至少选择一个套图类型");
      return;
    }

    startStrategyLoading({ snapshot: inputSnapshot });

    try {
      const result = await generateProductSuiteStrategy({
        images: inputSnapshot.images,
        platform: settings.platform,
        language: settings.language,
        product_input: settings.productInput,
        structure: suiteStructure.value,
      });

      if (result.code !== 0) {
        toast.error(result.message || "套图策略生成失败，请稍后重试");
        setStrategyStep("config");
        return;
      }

      const items = Array.isArray(result.data?.items) ? result.data.items : [];
      if (items.length === 0) {
        toast.error("AI 未返回有效套图策略");
        setStrategyStep("config");
        return;
      }

      const normalizedItems = normalizeSuiteStrategyItems(items);
      const brief =
        result.data?.brief ||
        `${settings.platform} / ${settings.language} / ${selectedImageLabel.value}，已为 ${normalizedItems.length} 个套图类型生成可编辑策略。`;
      setStrategyResult({
        brief,
        items: normalizedItems,
        snapshot: inputSnapshot,
      });
      toast.success("套图策略已生成，可编辑后继续出图");
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "套图策略生成失败，请稍后重试");
      }
      setStrategyStep("config");
    }
  }

  async function confirmStrategyAndGenerate() {
    if (suiteStrategyItems.value.length === 0) {
      toast.info("请先生成套图策略");
      return;
    }

    await generateSuiteImages();
  }

  async function generateSuiteImages() {
    const mainImg = uploadedImages.value[mainImageIndex.value];
    if (uploadedImages.value.length === 0) {
      toast.info("请先上传商品图片");
      return;
    }
    if (!mainImg || !mainImg.url) {
      toast.info("主图还未上传完成，请稍候再试");
      return;
    }
    if (hasUploadingImages(uploadedImages.value)) {
      toast.info("商品图还在上传中，请稍候");
      return;
    }
    if (!settings.productInput.trim()) {
      toast.info("请填写商品卖点与要求");
      return;
    }

    const queue = buildSuiteQueue();
    if (queue.length === 0) {
      toast.info("请至少保留一个套图策略");
      return;
    }

    const baseSettingsSnapshot = createGenerationSettingsSnapshot({
      scenario: "product_suite",
      platform: settings.platform,
      language: settings.language,
      ratio: settings.ratio,
      quality: settings.quality,
      scene: {
        structureConfig: suiteStructure.value,
        strategyBrief: strategyBrief.value,
      },
    });

    const snapshotPayload = {
      settings: baseSettingsSnapshot,
      source_images: cloneUploadedImages(uploadedImages.value),
      input_text: settings.productInput,
      structure: suiteStrategyItems.value,
    };

    const imageUrls = uploadedImages.value.map((img) => img.url).filter(Boolean);

    const ok = await enqueueImageBatch({
      queue,
      imageUrls,
      ratio: settings.ratio,
      resolution: settings.quality,
      snapshotPayload,
      initialLogs: ["商品套图生成任务初始化...", "读取商品图片、套图策略与平台规范..."],
      repeatLog: `新一批套图开始生成，共 ${queue.length} 张`,
      buildSettingsSnapshot: () => cloneGenerationSettingsSnapshot(baseSettingsSnapshot),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot }) {
        return createGenerationCard({
          typeId: item.id,
          strategyTitle: item.cardTitle,
          strategyContent: item.content || item.strategy,
          sortOrder,
          batchRunId,
          settingsSnapshot,
        });
      },
      buildUserPrompt: buildUserPromptForItem,
      getCreateLog: (item) => `正在生成 [${item.name}] 第 ${item.index} 张...`,
      getFailLogName: (item) => `${item.name} ${item.index}`,
      allFailedMessage: "所有套图任务都创建失败，请稍后重试",
    });

    if (ok || outputCards.value.length > 0) {
      setStrategyStep("result");
    }
  }

  function buildSuiteStrategySnapshot() {
    return {
      scenario: "product_suite",
      images: buildProductAnalyzeImages(uploadedImages.value, mainImageIndex.value),
      platform: settings.platform,
      language: settings.language,
      ratio: settings.ratio,
      quality: settings.quality,
      productInput: settings.productInput,
      structure: suiteStructure.value.map((item) => ({
        id: item.id,
        enabled: !!item.enabled,
        count: Number(item.count) || 0,
      })),
    };
  }

  function buildSuiteQueue() {
    return suiteStrategyItems.value.flatMap((item) => {
      const count = Math.max(0, Number(item.count) || 0);
      return Array.from({ length: count }, (_, index) => ({
        ...item,
        name: item.name || getStructureName(item.id),
        title: item.title || `${item.name || getStructureName(item.id)}策略`,
        content: item.content || "",
        strategy: item.strategy || getStructureStrategy(item.id),
        index: index + 1,
        total: count,
        cardTitle: count > 1 ? `${item.name || getStructureName(item.id)} ${index + 1}` : item.title || item.name,
      }));
    });
  }

  function buildUserPromptForItem(item) {
    const lines = [
      `【套图类型】${item.name}`,
      item.title ? `【策略标题】${item.title}` : "",
      item.strategy ? `【视觉策略】${item.strategy}` : "",
      item.content ? `【画面要求】${item.content}` : "",
      item.total > 1 ? `【本张序号】${item.index}/${item.total}，同类型多张图需要构图、角度或场景有区分。` : "",
    ];
    return lines.filter(Boolean).join("\n");
  }

  function normalizeSuiteStrategyItems(items) {
    return items.map((item, index) => {
      const fallback = suiteStructureDefaults.find((structure) => structure.id === item.id);
      const count = Math.max(1, Number(item.count) || fallback?.defaultCount || 1);
      return {
        id: item.id || fallback?.id || `suite-${index + 1}`,
        name: item.name || fallback?.name || `套图 ${index + 1}`,
        title: item.title || `${fallback?.name || "套图"}策略`,
        description: item.description || fallback?.description || "",
        strategy: item.strategy || fallback?.description || "",
        content: item.content || "",
        count,
        enabled: true,
      };
    });
  }

  function syncQualityForRatio() {
    const effectiveQuality = resolveQuality(settings.ratio, settings.quality) || settings.quality;
    if (effectiveQuality !== settings.quality) {
      settings.quality = effectiveQuality;
    }
  }

  function getStructureName(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.name || id || "商品套图";
  }

  function getStructureStrategy(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.description || "商品套图生成";
  }

  function findSuiteStrategyItem(typeId) {
    return suiteStrategyItems.value.find((item) => item.id === typeId) || {
      id: typeId,
      name: getStructureName(typeId),
      title: getStructureName(typeId),
      content: getStructureStrategy(typeId),
      strategy: getStructureStrategy(typeId),
    };
  }

  onBeforeUnmount(() => {
    runner.cleanup();
  });

  return {
    uploadedImages,
    mainImageIndex,
    aiLoading,
    workflowStep,
    strategyBrief,
    strategySnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    suiteStrategyItems,
    generating,
    creatingBatch,
    hasRunningTasks,
    generatedCount,
    runningCount,
    failedCount,
    jobTotal,
    genLogs,
    outputCards,
    zoomCard,
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    settings,
    suiteStructure,
    totalCount,
    configuredTotalCount,
    strategyTotalCount,
    hasGenerationSource,
    canGenerateStrategy,
    selectedCards,
    selectedCardsCount,
    selectedImageLabel,
    generateSellingPointsWithAI,
    triggerStrategyGeneration,
    confirmStrategyAndGenerate,
    generateSuiteImages,
    updateSuiteStrategyItem,
    reorderSuiteStrategyItems,
    removeSuiteStrategyItem,
    backToConfig,
    createNewTask,
    resetWorkspaceToDraft,
    updateCurrentJobTitle,
    loadHistoryTasks,
    loadGenerationJob,
    showNotice: toast.info,
    getStructureName,
    getStructureStrategy,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleImage,
    startPollingCard,
  };
}
