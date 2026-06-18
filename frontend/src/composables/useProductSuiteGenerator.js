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
import { buildProductAnalyzeImages } from "@/utils/analyzeImages.js";
import {
  cloneGenerationSettingsSnapshot,
  createGenerationSettingsSnapshot,
  getSnapshotValue,
} from "@/utils/generationSnapshots.js";

function createDefaultSuiteStructure() {
  return suiteStructureDefaults.map((item) => ({
    ...item,
    enabled: true,
    count: item.defaultCount,
  }));
}

export function useProductSuiteGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const genLogs = ref([]);

  // --- 通用卡片状态 + 轮询引擎 ---
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

  // --- 场景特有状态 ---
  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);

  const settings = reactive(createDefaultGenerationSettings());

  const suiteStructure = ref(createDefaultSuiteStructure());

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
    },
    applyJobData(data) {
      restoreSuiteJobData(data);
    },
    restoreCard(item) {
      return restoreGenerationCard(item, {
        strategyTitle: item.title || getStructureName(item.type_id),
        strategyContent: getStructureStrategy(item.type_id),
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

  // --- 通用卡片操作：选择 / 下载 ---
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

  // --- 计算属性 ---
  const totalCount = computed(() =>
    suiteStructure.value.reduce((sum, item) => {
      if (!item.enabled) return sum;
      return sum + item.count;
    }, 0),
  );
  const hasGenerationSource = computed(
    () => uploadedImages.value.length > 0 && settings.productInput.trim().length > 0,
  );
  const canGenerate = computed(
    () => hasGenerationSource.value && totalCount.value > 0 && !creatingBatch.value,
  );
  const selectedImageLabel = computed(() => {
    syncQualityForRatio();
    return formatImageLabel({ ratio: settings.ratio, quality: settings.quality });
  });

  function restoreSuiteJobData(data) {
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      const platform = getSnapshotValue(s, "platform");
      const language = getSnapshotValue(s, "language");
      const ratio = getSnapshotValue(s, "ratio");
      const quality = getSnapshotValue(s, "quality");
      if (typeof platform === "string") settings.platform = platform;
      if (typeof language === "string") settings.language = language;
      if (typeof ratio === "string" && resolutionMap[ratio]) {
        settings.ratio = ratio;
      }
      const desiredQuality = typeof quality === "string" ? quality : settings.quality;
      settings.quality = resolveQuality(settings.ratio, desiredQuality) || "1K";
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
      suiteStructure.value = data.structure;
    } else {
      suiteStructure.value = createDefaultSuiteStructure();
    }
  }

  // --- 生成套图 ---

  async function generateSuiteImages() {
    if (uploadedImages.value.length === 0) {
      toast.info("请先上传商品图片");
      return;
    }

    const mainImg = uploadedImages.value[mainImageIndex.value];
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

    const queue = buildSuiteQueue();
    if (queue.length === 0) {
      toast.info("请至少选择一个套图类型");
      return;
    }

    const baseSettingsSnapshot = createGenerationSettingsSnapshot({
      scenario: "product_suite",
      platform: settings.platform,
      language: settings.language,
      ratio: settings.ratio,
      quality: settings.quality,
      scene: {
        structure: suiteStructure.value,
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
      structure: suiteStructure.value,
    };

    const imageUrls = uploadedImages.value.map((img) => img.url).filter(Boolean);

    await enqueueImageBatch({
      queue,
      imageUrls,
      ratio: settings.ratio,
      resolution: settings.quality,
      snapshotPayload,
      initialLogs: ["商品套图生成任务初始化...", "读取商品图片、平台规范与套图结构..."],
      repeatLog: `新一批套图开始生成，共 ${queue.length} 张`,
      buildSettingsSnapshot: () => cloneGenerationSettingsSnapshot(baseSettingsSnapshot),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot }) {
        return createGenerationCard({
          typeId: item.id,
          strategyTitle: `${item.name} ${item.index}`,
          strategyContent: item.description,
          sortOrder,
          batchRunId,
          settingsSnapshot,
        });
      },
      getCreateLog: (item) => `正在生成 [${item.name}] 第 ${item.index} 张...`,
      getFailLogName: (item) => `${item.name} ${item.index}`,
      allFailedMessage: "所有套图任务都创建失败，请稍后重试",
    });
  }

  // --- 套图特有辅助 ---

  function buildSuiteQueue() {
    return suiteStructure.value.flatMap((item) => {
      if (!item.enabled) return [];
      return Array.from({ length: item.count }, (_, index) => ({
        id: item.id,
        name: item.name,
        description: item.description,
        index: index + 1,
      }));
    });
  }

  function syncQualityForRatio() {
    const effectiveQuality = resolveQuality(settings.ratio, settings.quality) || settings.quality;
    if (effectiveQuality !== settings.quality) {
      settings.quality = effectiveQuality;
    }
  }

  function getStructureName(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.name || id;
  }

  function getStructureStrategy(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.description || "商品套图生成";
  }

  // --- 生命周期 ---

  onBeforeUnmount(() => {
    runner.cleanup();
  });

  // --- 对外接口（保持与原版一致）---

  return {
    uploadedImages,
    mainImageIndex,
    aiLoading,
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
    hasGenerationSource,
    canGenerate,
    selectedCards,
    selectedCardsCount,
    selectedImageLabel,
    generateSellingPointsWithAI,
    generateSuiteImages,
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
