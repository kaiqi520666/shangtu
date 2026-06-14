import { computed, onBeforeUnmount, reactive, ref } from "vue";
import { ratioOptions, resolutionMap, resolveQuality } from "@/constants/generator.js";
import { suiteStructureDefaults } from "@/constants/productSuite.js";
import { useToast } from "@/composables/useToast.js";
import { useGenerationCards } from "@/composables/useGenerationCards.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { analyzeImage } from "@/api/image.js";

function createDefaultSuiteStructure() {
  return suiteStructureDefaults.map((item) => ({
    ...item,
    enabled: true,
    count: item.defaultCount,
  }));
}

export function useProductSuiteGenerator({ onJobCreated } = {}) {
  const toast = useToast();

  // --- 通用卡片状态 + 轮询引擎 ---
  const cards = useGenerationCards({
    getLogPrefix: (card) => card.strategyTitle || card.typeId || "",
    onBatchFinished({ total, failed }) {
      genLogs.value.push("全部商品套图任务已结束");
      if (failed === 0) {
        toast.success("商品套图已全部生成");
      } else if (failed === total) {
        toast.error("套图生成失败，请稍后重试");
      } else {
        toast.info(`部分套图生成失败（${failed} 张）`);
      }
    },
  });

  const {
    outputCards,
    genLogs,
    generating,
    generatedCount,
    jobTotal,
    startPollingCard,
    makeId,
  } = cards;

  // --- 场景特有状态 ---
  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);
  const aiLoading = ref(false);

  const settings = reactive({
    platform: "亚马逊",
    language: "中文",
    ratio: "1:1",
    quality: "1K",
    productInput: "",
  });

  const suiteStructure = ref(createDefaultSuiteStructure());

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
      return reactive({
        id: item.task_id,
        taskId: item.task_id,
        typeId: item.type_id || "",
        dataUrl: item.result_url || "",
        resultUrl: item.result_url || "",
        selected: true,
        status: item.status || "pending",
        strategyTitle: item.title || getStructureName(item.type_id),
        strategyContent: getStructureStrategy(item.type_id),
        errorMessage: item.error_message || "",
        sortOrder: item.sort_order || 0,
        batchRunId: "",
        creditRefunded: !!item.credit_refunded,
        userPrompt: item.user_prompt || "",
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
    () => hasGenerationSource.value && totalCount.value > 0 && !generating.value,
  );
  const selectedRatioOption = computed(
    () => ratioOptions.find((option) => option.value === settings.ratio) || ratioOptions[0],
  );
  const selectedImageLabel = computed(() => {
    const { width, height } = getCardSize();
    return `${settings.quality} / ${selectedRatioOption.value.label} / ${width}x${height}`;
  });

  function restoreSuiteJobData(data) {
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      if (typeof s.platform === "string") settings.platform = s.platform;
      if (typeof s.language === "string") settings.language = s.language;
      if (typeof s.ratio === "string" && resolutionMap[s.ratio]) {
        settings.ratio = s.ratio;
      }
      const desiredQuality = typeof s.quality === "string" ? s.quality : settings.quality;
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

  // --- AI 卖点分析 ---

  async function generateSellingPointsWithAI() {
    const mainImg = uploadedImages.value[mainImageIndex.value];
    if (!mainImg || !mainImg.url) {
      toast.info("请先上传商品图，等待图片上传完成后再让 AI 帮写");
      return "";
    }

    if (mainImg.uploading) {
      toast.info("主图还在上传中，请稍候");
      return "";
    }

    aiLoading.value = true;
    try {
      const result = await analyzeImage({
        image_url: mainImg.url,
        platform: settings.platform,
        scenario: "product_suite",
      });
      if (result.code !== 0) {
        toast.error(result.message || "AI 分析失败，请稍后重试");
        return "";
      }

      const content = result.data?.content?.trim();
      if (!content) {
        toast.error("AI 未返回有效内容");
        return "";
      }
      return content;
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "AI 分析失败，请稍后重试");
      }
      return "";
    } finally {
      aiLoading.value = false;
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

    const snapshotPayload = {
      settings: {
        platform: settings.platform,
        language: settings.language,
        ratio: settings.ratio,
        quality: settings.quality,
      },
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
      createCard({ item, sortOrder, batchRunId }) {
        return reactive({
          id: makeId(),
          taskId: "",
          typeId: item.id,
          dataUrl: "",
          resultUrl: "",
          selected: true,
          status: "pending",
          strategyTitle: `${item.name} ${item.index}`,
          strategyContent: item.description,
          errorMessage: "",
          sortOrder,
          batchRunId,
          creditRefunded: false,
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

  function getStructureName(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.name || id;
  }

  function getStructureStrategy(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.description || "商品套图生成";
  }

  function regenerateSingleCard(_card) {
    toast.info("请点击编辑图片按钮进行重新生成");
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
    generatedCount,
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
    regenerateSingleCard,
    startPollingCard,
  };
}
