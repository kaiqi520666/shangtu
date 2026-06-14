import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ratioOptions, resolutionMap, resolveQuality } from "@/constants/generator.js";
import { outfitPreviewSlides, scenePresets } from "@/constants/outfit.js";
import { listOutfitModels } from "@/api/outfit.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useGenerationCards } from "@/composables/useGenerationCards.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { useToast } from "@/composables/useToast.js";

export function useOutfitGenerator({ onJobCreated } = {}) {
  const toast = useToast();

  const cards = useGenerationCards({
    getLogPrefix: (card) => card.strategyTitle || card.typeId || "",
    onBatchFinished({ total, failed }) {
      genLogs.value.push("全部服饰穿搭任务已结束");
      if (failed === 0) {
        toast.success("服饰穿搭图已全部生成");
      } else if (failed === total) {
        toast.error("穿搭图生成失败，请稍后重试");
      } else {
        toast.info(`部分穿搭图生成失败（${failed} 张）`);
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

  const garmentImages = ref([]);
  const mainGarmentIndex = ref(0);
  const modelLibrary = ref([]);
  const modelsLoading = ref(false);
  const selectedModelId = ref("");
  const selectedScenes = ref(["street"]);
  const sceneDescription = ref("");

  const settings = reactive({
    platform: "亚马逊",
    language: "中文",
    ratio: "3:4",
    quality: "1K",
    productInput: "",
  });

  const runner = useGenerationRunner({
    scenario: "outfit",
    cards,
    toast,
    onJobCreated,
    resetSceneState() {
      garmentImages.value = [];
      mainGarmentIndex.value = 0;
      selectedScenes.value = ["street"];
      sceneDescription.value = "";
      settings.productInput = "";
    },
    applyJobData(data) {
      restoreOutfitJobData(data);
    },
    restoreCard(item) {
      const scene = findScene(item.type_id);
      return reactive({
        id: item.task_id,
        taskId: item.task_id,
        typeId: item.type_id || "",
        dataUrl: item.result_url || "",
        resultUrl: item.result_url || "",
        selected: true,
        status: item.status || "pending",
        strategyTitle: item.title || scene.label,
        strategyContent: scene.description,
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

  const actions = useCardActions({
    outputCards,
    currentTaskTitle,
    getCardName: (card) => card.strategyTitle || getSceneName(card.typeId),
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

  const selectedModel = computed(() =>
    modelLibrary.value.find((model) => model.id === selectedModelId.value),
  );
  const totalCount = computed(() => selectedScenes.value.length);
  const canGenerate = computed(
    () =>
      garmentImages.value.length > 0 &&
      Boolean(selectedModel.value?.image) &&
      selectedScenes.value.length > 0 &&
      !generating.value,
  );
  const selectedRatioOption = computed(
    () => ratioOptions.find((option) => option.value === settings.ratio) || ratioOptions[0],
  );
  const selectedImageLabel = computed(() => {
    const { width, height } = getCardSize();
    return `${settings.quality} / ${selectedRatioOption.value.label} / ${width}x${height}`;
  });
  const previewSlides = computed(() => {
    const uploadedImage = garmentImages.value[mainGarmentIndex.value];
    const src = getImageSrc(uploadedImage);
    if (!src) return outfitPreviewSlides;
    return outfitPreviewSlides.map((slide) => ({
      ...slide,
      sourceImage: src,
    }));
  });

  async function loadOutfitModels() {
    modelsLoading.value = true;
    try {
      const result = await listOutfitModels();
      if (result.code !== 0) {
        toast.error(result.message || "加载模特失败");
        modelLibrary.value = [];
        selectedModelId.value = "";
        return;
      }

      modelLibrary.value = (result.data || []).map((model) => ({
        id: model.id,
        name: model.name,
        image: model.image_url,
        objectKey: model.object_key,
        sortOrder: model.sort_order || 0,
      }));
      if (!selectedModelId.value && modelLibrary.value.length > 0) {
        selectedModelId.value = modelLibrary.value[0].id;
      }
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "加载模特失败");
      }
      modelLibrary.value = [];
      selectedModelId.value = "";
    } finally {
      modelsLoading.value = false;
    }
  }

  function restoreOutfitJobData(data) {
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      if (typeof s.platform === "string") settings.platform = s.platform;
      if (typeof s.language === "string") settings.language = s.language;
      if (typeof s.ratio === "string" && resolutionMap[s.ratio]) {
        settings.ratio = s.ratio;
      }
      const desiredQuality = typeof s.quality === "string" ? s.quality : settings.quality;
      settings.quality = resolveQuality(settings.ratio, desiredQuality) || "1K";
      if (Array.isArray(s.selectedScenes) && s.selectedScenes.length > 0) {
        selectedScenes.value = s.selectedScenes;
      }
      if (typeof s.sceneDescription === "string") {
        sceneDescription.value = s.sceneDescription;
      }
      if (typeof s.selectedModelId === "string") {
        selectedModelId.value = s.selectedModelId;
      }
    }

    if (Array.isArray(data.source_images)) {
      garmentImages.value = data.source_images.map((img) => ({
        ...img,
        previewUrl: img?.url || img?.previewUrl || "",
      }));
      mainGarmentIndex.value = 0;
    } else {
      garmentImages.value = [];
      mainGarmentIndex.value = 0;
    }

    settings.productInput = data.input_text || "";
    if (Array.isArray(data.structure) && data.structure.length > 0) {
      selectedScenes.value = data.structure.map((item) => item.id).filter(Boolean);
    }
  }

  async function generateOutfitImages() {
    const mainImg = garmentImages.value[mainGarmentIndex.value];
    if (garmentImages.value.length === 0) {
      toast.info("请先上传服装图片");
      return;
    }
    if (!mainImg || !mainImg.url) {
      toast.info("服装图还未上传完成，请稍候再试");
      return;
    }
    if (mainImg.uploading) {
      toast.info("服装图还在上传中，请稍候");
      return;
    }
    if (!selectedModel.value?.image) {
      toast.info("请选择模特形象");
      return;
    }
    const queue = buildOutfitQueue();
    if (queue.length === 0) {
      toast.info("请至少选择一个拍摄场景");
      return;
    }

    const snapshotPayload = {
      settings: {
        platform: settings.platform,
        language: settings.language,
        ratio: settings.ratio,
        quality: settings.quality,
        selectedScenes: selectedScenes.value,
        sceneDescription: sceneDescription.value,
        selectedModelId: selectedModel.value.id,
        selectedModelName: selectedModel.value.name,
        selectedModelImage: selectedModel.value.image,
      },
      source_images: garmentImages.value.map((img) => ({
        id: img.id,
        url: img.url,
        objectKey: img.objectKey,
        contentType: img.contentType,
        size: img.size,
        previewUrl: img.url || img.previewUrl,
      })),
      input_text: sceneDescription.value,
      structure: queue.map((item) => ({
        id: item.id,
        title: item.title,
        description: item.description,
      })),
    };

    await enqueueImageBatch({
      queue,
      imageUrls: [mainImg.url, selectedModel.value.image],
      ratio: settings.ratio,
      resolution: settings.quality,
      snapshotPayload,
      initialLogs: ["服饰穿搭生成任务初始化...", "读取服装图片、模特形象与拍摄场景..."],
      repeatLog: `新一批穿搭图开始生成，共 ${queue.length} 张`,
      createCard({ item, sortOrder, batchRunId }) {
        return reactive({
          id: makeId(),
          taskId: "",
          typeId: item.id,
          dataUrl: "",
          resultUrl: "",
          selected: true,
          status: "pending",
          strategyTitle: item.title,
          strategyContent: item.description,
          errorMessage: "",
          sortOrder,
          batchRunId,
          creditRefunded: false,
        });
      },
      getCreateLog: (item) => `正在生成 [${item.title}] 穿搭图...`,
      getFailLogName: (item) => item.title,
      allFailedMessage: "所有穿搭图任务都创建失败，请稍后重试",
    });
  }

  function buildOutfitQueue() {
    return selectedScenes.value.map((sceneId) => {
      const scene = findScene(sceneId);
      return {
        id: sceneId,
        title: scene.label,
        description: scene.description,
      };
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

  function findScene(id) {
    const preset = scenePresets.find((scene) => scene.id === id);
    return {
      id,
      label: preset?.label || id || "服饰穿搭图",
      description: getSceneStrategy(id),
    };
  }

  function getSceneName(id) {
    return findScene(id).label;
  }

  function getSceneStrategy(id) {
    const scene = scenePresets.find((item) => item.id === id);
    if (!scene) return "服饰穿搭场景生成";
    return `${scene.label}穿搭图，保持服装与模特参考一致，画面自然、清晰、适合电商展示。`;
  }

  function regenerateSingleCard(_card) {
    toast.info("请点击编辑图片按钮进行重新生成");
  }

  onMounted(() => {
    loadOutfitModels();
  });

  onBeforeUnmount(() => {
    runner.cleanup();
  });

  return {
    garmentImages,
    mainGarmentIndex,
    modelLibrary,
    modelsLoading,
    selectedModelId,
    selectedScenes,
    sceneDescription,
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    settings,
    generating,
    generatedCount,
    jobTotal,
    genLogs,
    outputCards,
    zoomCard,
    selectedModel,
    canGenerate,
    selectedCards,
    selectedCardsCount,
    totalCount,
    selectedImageLabel,
    previewSlides,
    showNotice: toast.info,
    loadOutfitModels,
    generateOutfitImages,
    getSceneName,
    getSceneStrategy,
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

function getImageSrc(image) {
  if (!image) return "";
  if (typeof image === "string") return image;
  return image.previewUrl || image.url || "";
}
