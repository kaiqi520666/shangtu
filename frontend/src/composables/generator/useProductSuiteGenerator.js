import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  createDefaultGenerationSettings,
  formatImageLabel,
} from "@/constants/generator.js";
import { useToast } from "@/composables/useToast.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/generator/useGenerationCards.js";
import { useAiSellingPointsWriter } from "@/composables/useAiSellingPointsWriter.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useMediaBatchRunner } from "@/composables/generator/batch/useMediaBatchRunner.js";
import { useGenerationStrategyFlow } from "@/composables/generator/strategy/useGenerationStrategyFlow.js";
import { buildProductAnalyzeImages, hasUploadingImages } from "@/utils/analyzeImages.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import {
  cloneGenerationSettingsSnapshot,
  cloneUploadedImages,
  createGenerationSettingsSnapshot,
  getSnapshotScene,
  restoreImageGenerationSettings,
  syncImageQuality,
} from "@/utils/generationSnapshots.js";
import { generateImageStrategy } from "@/api/image.js";
import { useCatalogStore } from "@/stores/catalog.js";

function createSuiteStructureFromCatalog(items) {
  return items.map((item) => ({
    ...item,
    enabled: true,
    count: item.defaultCount,
  }));
}

export function useProductSuiteGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const genLogs = ref([]);
  const catalog = useCatalogStore();
  const suiteCatalog = computed(() => catalog.suiteStructures);
  const catalogLoading = computed(() => catalog.loading);

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
  const suiteStructure = ref([]);

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
    runStrategy,
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

  const runner = useMediaBatchRunner({
    scenario: "product_suite",
    cards,
    toast,
    onJobCreated,
    resetSceneState() {
      uploadedImages.value = [];
      mainImageIndex.value = 0;
      settings.productInput = "";
      suiteStructure.value = createSuiteStructureFromCatalog(suiteCatalog.value);
      resetStrategy("config");
    },
    applyJobData(data) {
      restoreSuiteJobData(data);
    },
    restoreCard(item) {
      const strategyItem = findSuiteStrategyItem(item.type_id);
      return restoreGenerationCard(item, {
        strategyTitle: getStructureName(item.type_id),
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
    downloading,
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
      !catalogLoading.value &&
      !strategyLoading.value &&
      !creatingBatch.value &&
      !hasRunningTasks.value,
  );
  const selectedImageLabel = computed(() => {
    syncImageQuality(settings);
    return formatImageLabel({ ratio: settings.ratio, quality: settings.quality });
  });

  async function loadCatalog() {
    try {
      await catalog.ensureLoaded();
      syncSuiteStructureWithCatalog();
    } catch (error) {
      toast.error(error.response?.data?.message || "套图目录加载失败");
    }
  }

  function syncSuiteStructureWithCatalog() {
    suiteStructure.value = suiteCatalog.value.map((catalogItem) => {
      const current = suiteStructure.value.find((item) => item.id === catalogItem.id);
      return {
        ...catalogItem,
        enabled: current ? Boolean(current.enabled) : true,
        count: current ? clampStructureCount(current.count, catalogItem.maxCount) : catalogItem.defaultCount,
      };
    });
  }

  function clampStructureCount(count, maxCount) {
    return Math.min(Math.max(1, Number(count) || 1), maxCount);
  }

  function restoreSuiteJobData(data) {
    let restoredStrategyBrief = "";
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      const scene = getSnapshotScene(s);
      const { structureConfig, strategyBrief: nextStrategyBrief } = scene;
      restoredStrategyBrief = typeof nextStrategyBrief === "string" ? nextStrategyBrief : "";
      restoreImageGenerationSettings(settings, s);
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
    if (catalogLoading.value || suiteCatalog.value.length === 0) {
      toast.info("套图目录正在加载，请稍候");
      return;
    }

    const outcome = await runStrategy({
      snapshot: inputSnapshot,
      request: () => generateImageStrategy({
        scenario: inputSnapshot.scenario,
        images: inputSnapshot.images,
        platform: settings.platform,
        language: settings.language,
        product_input: settings.productInput,
        structure: suiteStructure.value,
      }),
      normalizeResult(data) {
        const items = normalizeSuiteStrategyItems(Array.isArray(data.items) ? data.items : []);
        return {
          brief: data.brief || `${settings.platform} / ${settings.language} / ${selectedImageLabel.value}，已为 ${items.length} 个套图类型生成可编辑策略。`,
          items,
        };
      },
      emptyMessage: "AI 未返回有效套图策略",
      failureMessage: "套图策略生成失败，请稍后重试",
    });
    if (!outcome.ok) {
      toast.error(outcome.error ? getApiErrorMessage(outcome.error, outcome.message) : outcome.message);
      return;
    }
    toast.success("套图策略已生成，可编辑后继续出图");
  }

  async function confirmStrategyAndGenerate() {
    if (suiteStrategyItems.value.length === 0) {
      toast.info("请先生成套图策略");
      return;
    }
    if (strategyDirty.value) {
      toast.info("配置已变化，请先更新套图策略");
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
        content: item.content || "",
        strategy: item.strategy || getStructureStrategy(item.id),
        index: index + 1,
        total: count,
        cardTitle: count > 1 ? `${item.name || getStructureName(item.id)} ${index + 1}` : item.name || getStructureName(item.id),
      }));
    });
  }

  function buildUserPromptForItem(item) {
    const lines = [
      `【套图类型】${item.name}`,
      item.strategy ? `【视觉策略】${item.strategy}` : "",
      item.content ? `【画面要求】${item.content}` : "",
      item.total > 1 ? `【本张序号】${item.index}/${item.total}，同类型多张图需要构图、角度或场景有区分。` : "",
    ];
    return lines.filter(Boolean).join("\n");
  }

  function normalizeSuiteStrategyItems(items) {
    return items.map((item, index) => {
      const fallback = catalog.findSuiteStructure(item.id);
      const count = Math.max(1, Number(item.count) || fallback?.defaultCount || 1);
      return {
        id: item.id || fallback?.id || `suite-${index + 1}`,
        name: item.name || fallback?.name || `套图 ${index + 1}`,
        description: item.description || fallback?.description || "",
        strategy: item.strategy || fallback?.strategy || "",
        content: item.content || "",
        count,
        enabled: true,
      };
    });
  }

  function getStructureName(id) {
    return catalog.findSuiteStructure(id)?.name || id || "商品套图";
  }

  function getStructureStrategy(id) {
    return catalog.findSuiteStructure(id)?.strategy || "商品套图生成";
  }

  function findSuiteStrategyItem(typeId) {
    return suiteStrategyItems.value.find((item) => item.id === typeId) || {
      id: typeId,
      name: getStructureName(typeId),
      content: getStructureStrategy(typeId),
      strategy: getStructureStrategy(typeId),
    };
  }

  onBeforeUnmount(() => {
    runner.cleanup();
  });

  onMounted(() => {
    loadCatalog();
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
    downloading,
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
    catalogLoading,
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
