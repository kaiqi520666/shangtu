import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  createDefaultGenerationSettings,
  formatImageLabel,
  resolutionMap,
  resolveQuality,
} from "@/constants/generator.js";
import { useCardActions } from "@/composables/useCardActions.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/useGenerationCards.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { useGenerationStrategyFlow } from "@/composables/useGenerationStrategyFlow.js";
import { useAiSellingPointsWriter } from "@/composables/useAiSellingPointsWriter.js";
import { useToast } from "@/composables/useToast.js";
import { buildProductAnalyzeImages, hasUploadingImages } from "@/utils/analyzeImages.js";
import {
  cloneGenerationSettingsSnapshot,
  createGenerationSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";
import { generateImageStrategy } from "@/api/image.js";
import { useCatalogStore } from "@/stores/catalog.js";

const DEFAULT_SELECTED_MODULES = [
  "first-screen",
  "core-selling",
  "use-scenario",
  "multi-angle",
  "detail-zoom",
  "ambient-scene",
];

function createDefaultSelectedModules() {
  return [...DEFAULT_SELECTED_MODULES];
}

export function useProductImageGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const genLogs = ref([]);
  const catalog = useCatalogStore();
  const availableModules = computed(() => catalog.modules);
  const catalogLoading = computed(() => catalog.loading);

  const cards = useGenerationCards({
    genLogs,
    getLogPrefix: (card) => card.strategyTitle || card.typeId || "",
    onBatchFinished: createBatchFinishedHandler({
      genLogs,
      toast,
      doneLog: "全部商品详情图任务已结束",
      successText: "商品详情图已全部生成",
      allFailedText: "详情图生成失败，请稍后重试",
      partialFailedText: (failed) => `部分详情图生成失败（${failed} 张）`,
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
  const selectedModules = ref(createDefaultSelectedModules());
  const settings = reactive(createDefaultGenerationSettings());

  const strategyFlow = useGenerationStrategyFlow({
    buildInputSnapshot: buildProductImageStrategySnapshot,
  });

  const {
    workflowStep,
    strategyBrief,
    strategyItems: moduleContents,
    strategySnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    startStrategyLoading,
    setStrategyResult,
    resetStrategy,
    setStrategyStep,
    updateStrategyItem: updateModuleContent,
    reorderStrategyItems: reorderModuleContents,
    removeStrategyItem: removeModuleContent,
    backToConfig,
  } = strategyFlow;

  const { aiLoading, generateSellingPointsWithAI } = useAiSellingPointsWriter({
    toast,
    buildImages: () => buildProductAnalyzeImages(uploadedImages.value, mainImageIndex.value),
    getUploadedImages: () => uploadedImages.value,
    getAnalyzePayload: () => ({
      platform: settings.platform,
      scenario: "product_image",
    }),
  });

  const runner = useGenerationRunner({
    scenario: "product_image",
    cards,
    toast,
    onJobCreated,
    resetSceneState() {
      uploadedImages.value = [];
      mainImageIndex.value = 0;
      selectedModules.value = createDefaultSelectedModules();
      settings.productInput = "";
      resetStrategy("config");
    },
    applyJobData(data) {
      restoreProductImageJobData(data);
    },
    restoreCard(item) {
      const moduleItem = findModuleContent(item.type_id);
      return restoreGenerationCard(item, {
        strategyTitle: getModuleName(item.type_id),
        strategyContent: moduleItem.content || moduleItem.strategy,
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
    getCardName: (card) => card.strategyTitle || getModuleName(card.typeId),
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

  const hasGenerationSource = computed(
    () => uploadedImages.value.length > 0 && settings.productInput.trim().length > 0,
  );
  const totalCount = computed(() =>
    moduleContents.value.length > 0 ? moduleContents.value.length : selectedModules.value.length,
  );
  const canGenerate = computed(
    () =>
      hasGenerationSource.value &&
      selectedModules.value.length > 0 &&
      availableModules.value.length > 0 &&
      !catalogLoading.value &&
      !creatingBatch.value &&
      !strategyLoading.value,
  );
  const canGenerateStrategy = computed(
    () =>
      hasGenerationSource.value &&
      selectedModules.value.length > 0 &&
      availableModules.value.length > 0 &&
      !catalogLoading.value &&
      !strategyLoading.value &&
      !creatingBatch.value &&
      !hasRunningTasks.value,
  );
  const selectedImageLabel = computed(() => {
    syncQualityForRatio();
    return formatImageLabel({ ratio: settings.ratio, quality: settings.quality });
  });

  async function loadCatalog() {
    try {
      await catalog.ensureLoaded();
      selectedModules.value = resolveSelectedModules(selectedModules.value);
    } catch (error) {
      toast.error(error.response?.data?.message || "图种目录加载失败");
    }
  }

  function resolveSelectedModules(moduleIds) {
    const catalogIds = availableModules.value.map((module) => module.id);
    const selected = moduleIds.filter((id) => catalogIds.includes(id));
    if (selected.length > 0) return selected;
    const defaults = DEFAULT_SELECTED_MODULES.filter((id) => catalogIds.includes(id));
    return defaults.length > 0 ? defaults : catalogIds.slice(0, 6);
  }

  function restoreProductImageJobData(data) {
    let restoredStrategyBrief = "";
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      const scene = getSnapshotScene(s);
      const { platform, language, ratio, quality } = s;
      const { selectedModules, strategyBrief: nextStrategyBrief } = scene;
      restoredStrategyBrief = typeof nextStrategyBrief === "string" ? nextStrategyBrief : "";
      if (typeof platform === "string") settings.platform = platform;
      if (typeof language === "string") settings.language = language;
      if (typeof ratio === "string" && resolutionMap[ratio]) {
        settings.ratio = ratio;
      }
      const desiredQuality = typeof quality === "string" ? quality : settings.quality;
      settings.quality = resolveQuality(settings.ratio, desiredQuality) || "1K";
      if (Array.isArray(selectedModules) && selectedModules.length > 0) {
        selectedModules.value = selectedModules;
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
      selectedModules.value = data.structure.map((item) => item.id).filter(Boolean);
      setStrategyResult({
        brief: restoredStrategyBrief,
        items: data.structure,
        snapshot: buildProductImageStrategySnapshot(),
        step: "result",
      });
    } else {
      resetStrategy("config");
    }
  }

  async function triggerStrategyGeneration() {
    const mainImg = uploadedImages.value[mainImageIndex.value];
    const inputSnapshot = buildProductImageStrategySnapshot();
    const images = inputSnapshot.images;
    if (hasRunningTasks.value) {
      toast.info("当前任务正在生成中，请稍后再生成模块策略");
      return;
    }
    if (creatingBatch.value) {
      toast.info("正在创建图片任务，请稍候");
      return;
    }
    if (!hasGenerationSource.value) {
      toast.info("请先上传产品图并填写商品卖点与要求");
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
    if (selectedModules.value.length === 0) {
      toast.info("请至少选择一个生成图种");
      return;
    }
    if (catalogLoading.value || availableModules.value.length === 0) {
      toast.info("图种目录正在加载，请稍候");
      return;
    }

    startStrategyLoading({ snapshot: inputSnapshot });

    try {
      const result = await generateImageStrategy({
        scenario: inputSnapshot.scenario,
        images,
        platform: settings.platform,
        language: settings.language,
        product_input: settings.productInput,
        module_ids: selectedModules.value,
      });

      if (result.code !== 0) {
        toast.error(result.message || "模块策略生成失败，请稍后重试");
        setStrategyStep("config");
        return;
      }

      const modules = Array.isArray(result.data?.modules) ? result.data.modules : [];
      if (modules.length === 0) {
        toast.error("AI 未返回有效模块策略");
        setStrategyStep("config");
        return;
      }

      const normalizedModules = normalizeStrategyModules(modules);
      selectedModules.value = normalizedModules.map((module) => module.id).filter(Boolean);
      const brief =
        result.data?.brief ||
        `${settings.platform} / ${settings.language} / ${selectedImageLabel.value}，已为 ${normalizedModules.length} 个图种生成可编辑模块内容。`;
      setStrategyResult({
        brief,
        items: normalizedModules,
        snapshot: inputSnapshot,
      });
      toast.success("模块策略已生成，可编辑后继续出图");
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "模块策略生成失败，请稍后重试");
      }
      setStrategyStep("config");
    }
  }

  async function confirmStrategyAndGenerate() {
    if (moduleContents.value.length === 0) {
      toast.info("请先生成模块策略");
      return;
    }

    await generateProductImages();
  }

  async function generateProductImages() {
    const mainImg = uploadedImages.value[mainImageIndex.value];
    if (uploadedImages.value.length === 0) {
      toast.info("请先上传产品图");
      return;
    }
    if (!mainImg || !mainImg.url) {
      toast.info("主图还未上传完成，请稍候再试");
      return;
    }
    if (mainImg.uploading) {
      toast.info("主图还在上传中，请稍候");
      return;
    }
    if (!settings.productInput.trim()) {
      toast.info("请填写商品卖点与要求");
      return;
    }

    const queue = buildProductImageQueue();
    if (queue.length === 0) {
      toast.info("请至少保留一个详情图策略");
      return;
    }

    const baseSettingsSnapshot = createGenerationSettingsSnapshot({
      scenario: "product_image",
      platform: settings.platform,
      language: settings.language,
      ratio: settings.ratio,
      quality: settings.quality,
      scene: {
        selectedModules: getActiveStrategyModuleIds(),
        strategyBrief: strategyBrief.value,
      },
    });

    const snapshotPayload = {
      settings: baseSettingsSnapshot,
      source_images: uploadedImages.value.map((img) => ({
        id: img.id,
        url: img.url,
        objectKey: img.objectKey,
        contentType: img.contentType,
        size: img.size,
        previewUrl: img.url || img.previewUrl,
      })),
      input_text: settings.productInput,
      structure: moduleContents.value,
    };

    const imageUrls = uploadedImages.value.map((img) => img.url).filter(Boolean);

    const ok = await enqueueImageBatch({
      queue,
      imageUrls,
      ratio: settings.ratio,
      resolution: settings.quality,
      snapshotPayload,
      initialLogs: ["商品详情图生成任务初始化...", "读取商品图片、模块策略与详情页结构..."],
      repeatLog: `新一批详情图开始生成，共 ${queue.length} 张`,
      buildSettingsSnapshot: () => cloneGenerationSettingsSnapshot(baseSettingsSnapshot),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot }) {
        return createGenerationCard({
          typeId: item.id,
          strategyTitle: item.moduleName,
          strategyContent: item.content || item.strategy,
          sortOrder,
          batchRunId,
          settingsSnapshot,
        });
      },
      buildUserPrompt: buildUserPromptForItem,
      getCreateLog: (item) => `正在生成 [${item.moduleName}]...`,
      getFailLogName: (item) => item.moduleName,
      allFailedMessage: "所有详情图任务都创建失败，请稍后重试",
    });

    if (ok || outputCards.value.length > 0) {
      setStrategyStep("result");
    }
  }

  function buildProductImageStrategySnapshot() {
    return {
      scenario: "product_image",
      images: buildProductAnalyzeImages(uploadedImages.value, mainImageIndex.value),
      platform: settings.platform,
      language: settings.language,
      ratio: settings.ratio,
      quality: settings.quality,
      productInput: settings.productInput,
      moduleIds: [...selectedModules.value],
    };
  }

  function getActiveStrategyModuleIds() {
    return moduleContents.value.length > 0
      ? moduleContents.value.map((module) => module.id).filter(Boolean)
      : selectedModules.value;
  }

  function buildProductImageQueue() {
    if (moduleContents.value.length > 0) {
      return moduleContents.value.map((item, index) => ({
        ...item,
        moduleName: item.moduleName || getModuleName(item.id),
        content: item.content || "",
        strategy: item.strategy || getModuleStrategy(item.id),
        index: index + 1,
      }));
    }

    return selectedModules.value.map((moduleId, index) => ({
      id: moduleId,
      moduleName: getModuleName(moduleId),
      content: getModuleStrategy(moduleId),
      strategy: getModuleStrategy(moduleId),
      index: index + 1,
    }));
  }

  function buildUserPromptForItem(item) {
    const lines = [
      `【图种】${item.moduleName}`,
      item.strategy ? `【视觉策略】${item.strategy}` : "",
      item.content ? `【模块内容】${item.content}` : "",
    ];
    return lines.filter(Boolean).join("\n");
  }

  function normalizeStrategyModules(modules) {
    return modules.map((module, index) => {
      const fallback = catalog.findModule(module.id);
      return {
        id: module.id || fallback?.id || `module-${index + 1}`,
        moduleName: module.moduleName || fallback?.name || `模块 ${index + 1}`,
        content: module.content || "",
        strategy: module.strategy || fallback?.strategy || "",
      };
    });
  }

  function getModuleName(id) {
    return catalog.findModule(id)?.name || id || "详情图";
  }

  function getModuleStrategy(id) {
    return catalog.findModule(id)?.strategy || "";
  }

  function syncQualityForRatio() {
    const effectiveQuality = resolveQuality(settings.ratio, settings.quality) || settings.quality;
    if (effectiveQuality !== settings.quality) {
      settings.quality = effectiveQuality;
    }
  }

  function findModuleContent(typeId) {
    return (
      moduleContents.value.find((module) => module.id === typeId) || {
        id: typeId,
        moduleName: getModuleName(typeId),
        content: getModuleStrategy(typeId),
        strategy: getModuleStrategy(typeId),
      }
    );
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
    selectedModules,
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    aiLoading,
    workflowStep,
    strategyBrief,
    strategySnapshot,
    strategyDirty,
    moduleContents,
    settings,
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
    canGenerate,
    canGenerateStrategy,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    selectedCards,
    selectedCardsCount,
    totalCount,
    selectedImageLabel,
    availableModules,
    catalogLoading,
    showNotice: toast.info,
    generateSellingPointsWithAI,
    hasGenerationSource,
    getModuleName,
    getModuleStrategy,
    triggerStrategyGeneration,
    confirmStrategyAndGenerate,
    generateProductImages,
    updateModuleContent,
    reorderModuleContents,
    removeModuleContent,
    backToConfig,
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
