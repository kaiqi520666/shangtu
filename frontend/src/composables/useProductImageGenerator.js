import { computed, onBeforeUnmount, reactive, ref } from "vue";
import { availableModules, ratioOptions, resolutionMap, resolveQuality } from "@/constants/generator.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useGenerationCards } from "@/composables/useGenerationCards.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { useToast } from "@/composables/useToast.js";
import { analyzeImage, generateProductImageStrategy } from "@/api/image.js";

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

  const cards = useGenerationCards({
    getLogPrefix: (card) => card.strategyTitle || card.typeId || "",
    onBatchFinished({ total, failed }) {
      genLogs.value.push("全部商品详情图任务已结束");
      if (failed === 0) {
        toast.success("商品详情图已全部生成");
      } else if (failed === total) {
        toast.error("详情图生成失败，请稍后重试");
      } else {
        toast.info(`部分详情图生成失败（${failed} 张）`);
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

  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);
  const selectedModules = ref(createDefaultSelectedModules());
  const aiLoading = ref(false);
  const workflowStep = ref("config");
  const strategyBrief = ref("");
  const moduleContents = ref([]);

  const settings = reactive({
    platform: "亚马逊",
    language: "中文",
    ratio: "1:1",
    quality: "1K",
    productInput: "",
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
      strategyBrief.value = "";
      moduleContents.value = [];
      workflowStep.value = "config";
    },
    applyJobData(data) {
      restoreProductImageJobData(data);
    },
    restoreCard(item) {
      const moduleItem = findModuleContent(item.type_id, item.title);
      return reactive({
        id: item.task_id,
        taskId: item.task_id,
        typeId: item.type_id || "",
        dataUrl: item.result_url || "",
        resultUrl: item.result_url || "",
        selected: true,
        status: item.status || "pending",
        strategyTitle: item.title || moduleItem.title,
        strategyContent: moduleItem.content || moduleItem.strategy,
        errorMessage: item.error_message || "",
        sortOrder: item.sort_order || 0,
        batchRunId: "",
        creditRefunded: !!item.credit_refunded,
        editInstruction: item.edit_instruction || "",
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

  const strategyLoading = computed(() => workflowStep.value === "strategy-loading");
  const strategyPanelVisible = computed(
    () => workflowStep.value === "strategy-loading" || workflowStep.value === "strategy-review",
  );
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
      !generating.value &&
      !strategyLoading.value,
  );
  const selectedRatioOption = computed(
    () => ratioOptions.find((option) => option.value === settings.ratio) || ratioOptions[0],
  );
  const selectedImageLabel = computed(() => {
    const { width, height } = getCardSize();
    return `${settings.quality} / ${selectedRatioOption.value.label} / ${width}x${height}`;
  });

  function restoreProductImageJobData(data) {
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      if (typeof s.platform === "string") settings.platform = s.platform;
      if (typeof s.language === "string") settings.language = s.language;
      if (typeof s.ratio === "string" && resolutionMap[s.ratio]) {
        settings.ratio = s.ratio;
      }
      const desiredQuality = typeof s.quality === "string" ? s.quality : settings.quality;
      settings.quality = resolveQuality(settings.ratio, desiredQuality) || "1K";
      if (Array.isArray(s.selectedModules) && s.selectedModules.length > 0) {
        selectedModules.value = s.selectedModules;
      }
      if (typeof s.strategyBrief === "string") {
        strategyBrief.value = s.strategyBrief;
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
      moduleContents.value = data.structure;
      selectedModules.value = data.structure.map((item) => item.id).filter(Boolean);
      workflowStep.value = "result";
    } else {
      moduleContents.value = [];
      workflowStep.value = "config";
    }
  }

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

  async function triggerStrategyGeneration() {
    const mainImg = uploadedImages.value[mainImageIndex.value];
    if (!hasGenerationSource.value) {
      toast.info("请先上传产品图并填写商品卖点与要求");
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
    if (selectedModules.value.length === 0) {
      toast.info("请至少选择一个生成图种");
      return;
    }

    workflowStep.value = "strategy-loading";
    strategyBrief.value = "";
    moduleContents.value = [];

    try {
      const result = await generateProductImageStrategy({
        image_url: mainImg.url,
        platform: settings.platform,
        language: settings.language,
        product_input: settings.productInput,
        module_ids: selectedModules.value,
      });

      if (result.code !== 0) {
        toast.error(result.message || "模块策略生成失败，请稍后重试");
        workflowStep.value = "config";
        return;
      }

      const modules = Array.isArray(result.data?.modules) ? result.data.modules : [];
      if (modules.length === 0) {
        toast.error("AI 未返回有效模块策略");
        workflowStep.value = "config";
        return;
      }

      moduleContents.value = normalizeStrategyModules(modules);
      selectedModules.value = moduleContents.value.map((module) => module.id);
      strategyBrief.value =
        result.data?.brief ||
        `${settings.platform} / ${settings.language} / ${selectedImageLabel.value}，已为 ${moduleContents.value.length} 个图种生成可编辑模块内容。`;
      workflowStep.value = "strategy-review";
      toast.success("模块策略已生成，可编辑后继续出图");
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "模块策略生成失败，请稍后重试");
      }
      workflowStep.value = "config";
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

    const snapshotPayload = {
      settings: {
        platform: settings.platform,
        language: settings.language,
        ratio: settings.ratio,
        quality: settings.quality,
        selectedModules: selectedModules.value,
        strategyBrief: strategyBrief.value,
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
      structure: moduleContents.value,
    };

    const ok = await enqueueImageBatch({
      queue,
      imageUrl: mainImg.url,
      ratio: settings.ratio,
      resolution: settings.quality,
      snapshotPayload,
      initialLogs: ["商品详情图生成任务初始化...", "读取商品图片、模块策略与详情页结构..."],
      repeatLog: `新一批详情图开始生成，共 ${queue.length} 张`,
      createCard({ item, sortOrder, batchRunId }) {
        return reactive({
          id: makeId(),
          taskId: "",
          typeId: item.id,
          dataUrl: "",
          resultUrl: "",
          selected: true,
          status: "pending",
          strategyTitle: item.title || item.moduleName,
          strategyContent: item.content || item.strategy,
          errorMessage: "",
          sortOrder,
          batchRunId,
          creditRefunded: false,
        });
      },
      buildPrompt: buildPromptForItem,
      getCreateLog: (item) => `正在生成 [${item.moduleName}]...`,
      getFailLogName: (item) => item.moduleName,
      allFailedMessage: "所有详情图任务都创建失败，请稍后重试",
    });

    if (ok || outputCards.value.length > 0) {
      workflowStep.value = "result";
    }
  }

  function buildProductImageQueue() {
    if (moduleContents.value.length > 0) {
      return moduleContents.value.map((item, index) => ({
        ...item,
        moduleName: item.moduleName || getModuleName(item.id),
        title: item.title || getModuleName(item.id),
        content: item.content || "",
        strategy: item.strategy || getModuleStrategy(item.id),
        index: index + 1,
      }));
    }

    return selectedModules.value.map((moduleId, index) => ({
      id: moduleId,
      moduleName: getModuleName(moduleId),
      title: getModuleName(moduleId),
      content: getModuleStrategy(moduleId),
      strategy: getModuleStrategy(moduleId),
      index: index + 1,
    }));
  }

  function buildPromptForItem(item) {
    const lines = [
      "【参考图】必须以用户上传的商品图为商品主体，保持商品款式、颜色、材质、结构和外观完全一致。",
      "【任务】生成一张电商商品详情页模块图，不要生成整张长详情页。",
      `【投放平台】${settings.platform}`,
      `【排版语言】${settings.language}`,
      `【画面比例】${settings.ratio}`,
      `【详情图模块】${item.moduleName}`,
      `【模块标题】${item.title}`,
      item.strategy ? `【视觉策略】${item.strategy}` : "",
      item.content ? `【模块内容】${item.content}` : "",
      "【商品卖点与要求】",
      settings.productInput.trim(),
      "【强约束】禁止虚构品牌 Logo、认证标识、价格、销量、参数等无法从参考图与上述卖点确认的信息；如需添加文字必须使用上述指定语言，文字简洁清晰，适合电商详情页展示。",
    ];
    return lines.filter(Boolean).join("\n");
  }

  function normalizeStrategyModules(modules) {
    return modules.map((module, index) => {
      const fallback = availableModules.find((item) => item.id === module.id);
      return {
        id: module.id || fallback?.id || `module-${index + 1}`,
        moduleName: module.moduleName || fallback?.name || `模块 ${index + 1}`,
        title: module.title || `${fallback?.name || "详情图"}策略`,
        content: module.content || "",
        strategy: module.strategy || fallback?.strategy || "",
      };
    });
  }

  function updateModuleContent(index, patch) {
    const current = moduleContents.value[index];
    if (!current) return;
    moduleContents.value[index] = {
      ...current,
      ...patch,
    };
  }

  function reorderModuleContents(nextModules) {
    moduleContents.value = nextModules;
    selectedModules.value = nextModules.map((module) => module.id).filter(Boolean);
  }

  function removeModuleContent(index) {
    moduleContents.value = moduleContents.value.filter((_, currentIndex) => currentIndex !== index);
    selectedModules.value = moduleContents.value.map((module) => module.id).filter(Boolean);
  }

  function backToConfig() {
    workflowStep.value = "config";
  }

  function getModuleName(id) {
    return availableModules.find((module) => module.id === id)?.name || id || "详情图";
  }

  function getModuleStrategy(id) {
    return availableModules.find((module) => module.id === id)?.strategy || "";
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

  function findModuleContent(typeId, title = "") {
    return (
      moduleContents.value.find((module) => module.id === typeId && (!title || module.title === title)) ||
      moduleContents.value.find((module) => module.id === typeId) || {
        id: typeId,
        moduleName: getModuleName(typeId),
        title: title || getModuleName(typeId),
        content: getModuleStrategy(typeId),
        strategy: getModuleStrategy(typeId),
      }
    );
  }

  function regenerateSingleCard(_card) {
    toast.info("请点击编辑图片按钮进行重新生成");
  }

  onBeforeUnmount(() => {
    runner.cleanup();
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
    moduleContents,
    settings,
    generating,
    generatedCount,
    jobTotal,
    genLogs,
    outputCards,
    zoomCard,
    canGenerate,
    strategyLoading,
    strategyPanelVisible,
    selectedCards,
    selectedCardsCount,
    totalCount,
    selectedImageLabel,
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
    regenerateSingleCard,
    createNewTask,
    resetWorkspaceToDraft,
    updateCurrentJobTitle,
    loadHistoryTasks,
    loadGenerationJob,
    startPollingCard,
  };
}
