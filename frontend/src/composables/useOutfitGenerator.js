import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  createDefaultGenerationSettings,
  formatImageLabel,
  resolutionMap,
  resolveQuality,
} from "@/constants/generator.js";
import { outfitPreviewSlides, scenePresets } from "@/constants/outfit.js";
import { deleteOutfitModel, listOutfitModels, uploadOutfitModel } from "@/api/outfit.js";
import { useCardActions } from "@/composables/useCardActions.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/useGenerationCards.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { useToast } from "@/composables/useToast.js";
import {
  cloneGenerationSettingsSnapshot,
  createGenerationSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";

export function useOutfitGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const genLogs = ref([]);

  const cards = useGenerationCards({
    genLogs,
    getLogPrefix: (card) => card.strategyTitle || card.typeId || "",
    onBatchFinished: createBatchFinishedHandler({
      genLogs,
      toast,
      doneLog: "全部服饰穿搭任务已结束",
      successText: "服饰穿搭图已全部生成",
      allFailedText: "穿搭图生成失败，请稍后重试",
      partialFailedText: (failed) => `部分穿搭图生成失败（${failed} 张）`,
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

  const garmentImages = ref([]);
  const mainGarmentIndex = ref(0);
  const modelLibrary = ref([]);
  const modelsLoading = ref(false);
  const modelUploading = ref(false);
  const modelDeletingId = ref("");
  const selectedModelId = ref("");
  const selectedScenes = ref(["street"]);
  const sceneDescription = ref("");

  const settings = reactive(createDefaultGenerationSettings({ ratio: "3:4" }));

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
      return restoreGenerationCard(item, {
        strategyTitle: item.title || scene.label,
        strategyContent: scene.description,
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
      !creatingBatch.value,
  );
  const selectedImageLabel = computed(() => {
    syncQualityForRatio();
    return formatImageLabel({ ratio: settings.ratio, quality: settings.quality });
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

      modelLibrary.value = (result.data || []).map(normalizeModel);
      if (
        (!selectedModelId.value ||
          !modelLibrary.value.some((model) => model.id === selectedModelId.value)) &&
        modelLibrary.value.length > 0
      ) {
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

  async function uploadModel(file) {
    if (!file) return;
    modelUploading.value = true;
    try {
      const result = await uploadOutfitModel(file);
      if (result.code !== 0) {
        toast.error(result.message || "模特上传失败");
        return;
      }

      const model = normalizeModel(result.data);
      modelLibrary.value = [model, ...modelLibrary.value];
      selectedModelId.value = model.id;
      toast.success("模特已上传");
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "模特上传失败");
      }
    } finally {
      modelUploading.value = false;
    }
  }

  async function deleteModel(modelId) {
    const model = modelLibrary.value.find((item) => item.id === modelId);
    if (!model || !model.canDelete) {
      toast.info("系统默认模特不能删除");
      return;
    }

    modelDeletingId.value = modelId;
    try {
      const result = await deleteOutfitModel(modelId);
      if (result.code !== 0) {
        toast.error(result.message || "删除模特失败");
        return;
      }

      modelLibrary.value = modelLibrary.value.filter((item) => item.id !== modelId);
      if (selectedModelId.value === modelId) {
        selectedModelId.value = modelLibrary.value[0]?.id || "";
      }
      toast.success("模特已删除");
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "删除模特失败");
      }
    } finally {
      modelDeletingId.value = "";
    }
  }

  function restoreOutfitJobData(data) {
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      const scene = getSnapshotScene(s);
      const { platform, language, ratio, quality } = s;
      const {
        selectedScenes: nextSelectedScenes,
        sceneDescription: nextSceneDescription,
        selectedModelId: nextSelectedModelId,
      } = scene;
      if (typeof platform === "string") settings.platform = platform;
      if (typeof language === "string") settings.language = language;
      if (typeof ratio === "string" && resolutionMap[ratio]) {
        settings.ratio = ratio;
      }
      const desiredQuality = typeof quality === "string" ? quality : settings.quality;
      settings.quality = resolveQuality(settings.ratio, desiredQuality) || "1K";
      if (Array.isArray(nextSelectedScenes) && nextSelectedScenes.length > 0) {
        selectedScenes.value = nextSelectedScenes;
      }
      if (typeof nextSceneDescription === "string") {
        sceneDescription.value = nextSceneDescription;
      }
      if (typeof nextSelectedModelId === "string") {
        selectedModelId.value = nextSelectedModelId;
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

    const baseSettingsSnapshot = createGenerationSettingsSnapshot({
      scenario: "outfit",
      platform: settings.platform,
      language: settings.language,
      ratio: settings.ratio,
      quality: settings.quality,
      scene: {
        selectedScenes: selectedScenes.value,
        sceneDescription: sceneDescription.value,
        selectedModelId: selectedModel.value.id,
        selectedModelName: selectedModel.value.name,
        selectedModelImage: selectedModel.value.image,
      },
    });

    const snapshotPayload = {
      settings: baseSettingsSnapshot,
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
      buildSettingsSnapshot: () => cloneGenerationSettingsSnapshot(baseSettingsSnapshot),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot }) {
        return createGenerationCard({
          typeId: item.id,
          strategyTitle: item.title,
          strategyContent: item.description,
          sortOrder,
          batchRunId,
          settingsSnapshot,
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

  function syncQualityForRatio() {
    const effectiveQuality = resolveQuality(settings.ratio, settings.quality) || settings.quality;
    if (effectiveQuality !== settings.quality) {
      settings.quality = effectiveQuality;
    }
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
    modelUploading,
    modelDeletingId,
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
    creatingBatch,
    hasRunningTasks,
    generatedCount,
    runningCount,
    failedCount,
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
    uploadModel,
    deleteModel,
    generateOutfitImages,
    getSceneName,
    getSceneStrategy,
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

function getImageSrc(image) {
  if (!image) return "";
  if (typeof image === "string") return image;
  return image.previewUrl || image.url || "";
}

function normalizeModel(model) {
  return {
    id: model.id,
    name: model.name,
    image: model.image_url,
    objectKey: model.object_key,
    sortOrder: model.sort_order || 0,
    isSystem: Boolean(model.is_system),
    canDelete: Boolean(model.can_delete),
    createdAt: model.created_at || "",
  };
}
