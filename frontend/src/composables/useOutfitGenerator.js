import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  createDefaultGenerationSettings,
  formatImageLabel,
  resolutionMap,
  resolveQuality,
} from "@/constants/generator.js";
import { outfitPreviewSlides } from "@/constants/outfit.js";
import { generateImageStrategy } from "@/api/image.js";
import { deleteOutfitModel, listOutfitModels, uploadOutfitModel } from "@/api/outfit.js";
import { useCardActions } from "@/composables/useCardActions.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/useGenerationCards.js";
import { useGenerationRunner } from "@/composables/useGenerationRunner.js";
import { useGenerationStrategyFlow } from "@/composables/useGenerationStrategyFlow.js";
import { useToast } from "@/composables/useToast.js";
import {
  cloneGenerationSettingsSnapshot,
  createGenerationSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";
import { buildOutfitAnalyzeImages, hasUploadingImages } from "@/utils/analyzeImages.js";
import { useCatalogStore } from "@/stores/catalog.js";

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

export function useOutfitGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const genLogs = ref([]);
  const catalog = useCatalogStore();
  const outfitScenes = computed(() => catalog.outfitScenes);
  const catalogLoading = computed(() => catalog.loading);

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
  const restoredModelSnapshot = ref(null);
  const selectedScenes = ref([]);
  const sceneDescription = ref("");
  const settings = reactive(createDefaultGenerationSettings({ ratio: "3:4" }));

  const selectedModel = computed(() =>
    modelLibrary.value.find((model) => model.id === selectedModelId.value) ||
    (restoredModelSnapshot.value?.id === selectedModelId.value ? restoredModelSnapshot.value : null),
  );

  const strategyFlow = useGenerationStrategyFlow({
    buildInputSnapshot: buildOutfitStrategySnapshot,
  });

  const {
    workflowStep,
    strategyBrief,
    strategyItems: outfitStrategyItems,
    strategySnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    startStrategyLoading,
    setStrategyResult,
    resetStrategy,
    setStrategyStep,
    updateStrategyItem: updateOutfitStrategyItem,
    reorderStrategyItems: reorderOutfitStrategyItems,
    removeStrategyItem: removeOutfitStrategyItem,
    backToConfig,
  } = strategyFlow;

  const runner = useGenerationRunner({
    scenario: "outfit",
    cards,
    toast,
    onJobCreated,
    resetSceneState() {
      garmentImages.value = [];
      mainGarmentIndex.value = 0;
      selectedScenes.value = createDefaultSelectedScenes();
      sceneDescription.value = "";
      restoredModelSnapshot.value = null;
      settings.productInput = "";
      resetStrategy("config");
    },
    applyJobData(data) {
      restoreOutfitJobData(data);
    },
    restoreCard(item) {
      const strategyItem = findOutfitStrategyItem(item.type_id);
      return restoreGenerationCard(item, {
        strategyTitle: getSceneName(item.type_id),
        strategyContent: strategyItem.content || strategyItem.strategy || getSceneStrategy(item.type_id),
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

  const configuredTotalCount = computed(() => selectedScenes.value.length);
  const strategyTotalCount = computed(() => outfitStrategyItems.value.length);
  const totalCount = computed(() => strategyTotalCount.value || configuredTotalCount.value);
  const hasGenerationSource = computed(
    () => garmentImages.value.length > 0 && Boolean(selectedModel.value?.image),
  );
  const canGenerateStrategy = computed(
    () =>
      hasGenerationSource.value &&
      selectedScenes.value.length > 0 &&
      !modelsLoading.value &&
      !catalogLoading.value &&
      !strategyLoading.value &&
      !creatingBatch.value &&
      !hasRunningTasks.value,
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

  function createDefaultSelectedScenes() {
    return outfitScenes.value[0]?.id ? [outfitScenes.value[0].id] : [];
  }

  async function loadCatalog() {
    try {
      await catalog.ensureLoaded();
      selectedScenes.value = resolveSelectedScenes(selectedScenes.value);
    } catch (error) {
      toast.error(error.response?.data?.message || "穿搭场景目录加载失败");
    }
  }

  function resolveSelectedScenes(sceneIds) {
    const catalogIds = outfitScenes.value.map((scene) => scene.id);
    const selected = sceneIds.filter((id) => catalogIds.includes(id));
    if (selected.length > 0) return selected;
    return createDefaultSelectedScenes();
  }

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
      if (!selectedModel.value && modelLibrary.value.length > 0) {
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
    let restoredStrategyBrief = "";
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      const scene = getSnapshotScene(s);
      const { platform, language, ratio, quality } = s;
      const {
        selectedScenes: nextSelectedScenes,
        sceneDescription: nextSceneDescription,
        selectedModelId: nextSelectedModelId,
        selectedModelName: nextSelectedModelName,
        selectedModelImage: nextSelectedModelImage,
        strategyBrief: nextStrategyBrief,
      } = scene;
      restoredStrategyBrief = typeof nextStrategyBrief === "string" ? nextStrategyBrief : "";
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
        if (typeof nextSelectedModelImage === "string" && nextSelectedModelImage) {
          restoredModelSnapshot.value = {
            id: nextSelectedModelId,
            name: typeof nextSelectedModelName === "string" ? nextSelectedModelName : "已恢复模特",
            image: nextSelectedModelImage,
          };
        }
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
      setStrategyResult({
        brief: restoredStrategyBrief,
        items: normalizeOutfitStrategyItems(data.structure),
        snapshot: buildOutfitStrategySnapshot(),
        step: "result",
      });
    } else {
      resetStrategy("config");
    }
  }

  async function triggerStrategyGeneration() {
    const mainImg = garmentImages.value[mainGarmentIndex.value];
    const inputSnapshot = buildOutfitStrategySnapshot();
    if (hasRunningTasks.value) {
      toast.info("当前任务正在生成中，请稍后再生成穿搭策略");
      return;
    }
    if (creatingBatch.value) {
      toast.info("正在创建图片任务，请稍候");
      return;
    }
    if (garmentImages.value.length === 0) {
      toast.info("请先上传服装图片");
      return;
    }
    if (!mainImg || !mainImg.url) {
      toast.info("服装图还未上传完成，请稍候再试");
      return;
    }
    if (hasUploadingImages(garmentImages.value)) {
      toast.info("服装图还在上传中，请稍候");
      return;
    }
    if (!selectedModel.value?.image) {
      toast.info("请选择模特形象");
      return;
    }
    if (selectedScenes.value.length === 0) {
      toast.info("请至少选择一个拍摄场景");
      return;
    }
    if (catalogLoading.value || outfitScenes.value.length === 0) {
      toast.info("拍摄场景目录正在加载，请稍候");
      return;
    }

    startStrategyLoading({ snapshot: inputSnapshot });

    try {
      const result = await generateImageStrategy({
        scenario: inputSnapshot.scenario,
        images: inputSnapshot.images,
        platform: settings.platform,
        language: settings.language,
        scene_description: sceneDescription.value,
        selected_model_name: selectedModel.value.name,
        scene_ids: selectedScenes.value,
      });

      if (result.code !== 0) {
        toast.error(result.message || "穿搭策略生成失败，请稍后重试");
        setStrategyStep("config");
        return;
      }

      const items = Array.isArray(result.data?.items) ? result.data.items : [];
      if (items.length === 0) {
        toast.error("AI 未返回有效穿搭策略");
        setStrategyStep("config");
        return;
      }

      const normalizedItems = normalizeOutfitStrategyItems(items);
      const brief =
        result.data?.brief ||
        `${settings.platform} / ${settings.language} / ${selectedImageLabel.value}，已为 ${normalizedItems.length} 个场景生成可编辑穿搭策略。`;
      setStrategyResult({
        brief,
        items: normalizedItems,
        snapshot: inputSnapshot,
      });
      toast.success("穿搭策略已生成，可编辑后继续出图");
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "穿搭策略生成失败，请稍后重试");
      }
      setStrategyStep("config");
    }
  }

  async function confirmStrategyAndGenerate() {
    if (outfitStrategyItems.value.length === 0) {
      toast.info("请先生成穿搭策略");
      return;
    }

    await generateOutfitImages();
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
    if (hasUploadingImages(garmentImages.value)) {
      toast.info("服装图还在上传中，请稍候");
      return;
    }
    if (!selectedModel.value?.image) {
      toast.info("请选择模特形象");
      return;
    }
    const queue = buildOutfitQueue();
    if (queue.length === 0) {
      toast.info("请至少保留一个穿搭策略");
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
        strategyBrief: strategyBrief.value,
      },
    });

    const snapshotPayload = {
      settings: baseSettingsSnapshot,
      source_images: cloneUploadedImages(garmentImages.value),
      input_text: sceneDescription.value,
      structure: outfitStrategyItems.value,
    };

    const ok = await enqueueImageBatch({
      queue,
      imageUrls: [mainImg.url, selectedModel.value.image],
      ratio: settings.ratio,
      resolution: settings.quality,
      snapshotPayload,
      initialLogs: ["服饰穿搭生成任务初始化...", "读取服装图片、模特形象与穿搭策略..."],
      repeatLog: `新一批穿搭图开始生成，共 ${queue.length} 张`,
      buildSettingsSnapshot: () => cloneGenerationSettingsSnapshot(baseSettingsSnapshot),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot }) {
        return createGenerationCard({
          typeId: item.id,
          strategyTitle: item.name,
          strategyContent: item.content || item.fidelity || item.strategy,
          sortOrder,
          batchRunId,
          settingsSnapshot,
        });
      },
      buildUserPrompt: buildUserPromptForItem,
      getCreateLog: (item) => `正在生成 [${item.name}] 穿搭图...`,
      getFailLogName: (item) => item.name,
      allFailedMessage: "所有穿搭图任务都创建失败，请稍后重试",
    });

    if (ok || outputCards.value.length > 0) {
      setStrategyStep("result");
    }
  }

  function buildOutfitStrategySnapshot() {
    return {
      scenario: "outfit",
      images: buildOutfitAnalyzeImages(
        garmentImages.value,
        mainGarmentIndex.value,
        selectedModel.value,
      ),
      platform: settings.platform,
      language: settings.language,
      ratio: settings.ratio,
      quality: settings.quality,
      selectedModelId: selectedModel.value?.id || "",
      selectedModelName: selectedModel.value?.name || "",
      selectedScenes: [...selectedScenes.value],
      sceneDescription: sceneDescription.value,
    };
  }

  function buildOutfitQueue() {
    return outfitStrategyItems.value.map((item, index) => ({
      ...item,
      id: item.id,
      name: item.name || getSceneName(item.id),
      content: composeOutfitStrategyContent(item),
      strategy: item.strategy || getSceneStrategy(item.id),
      index: index + 1,
    }));
  }

  function buildUserPromptForItem(item) {
    const lines = [
      `【拍摄场景】${item.name}`,
      item.strategy ? `【场景策略】${item.strategy}` : "",
      item.pose ? `【模特姿态】${item.pose}` : "",
      item.camera ? `【镜头角度】${item.camera}` : "",
      item.fidelity ? `【服装保真约束】${item.fidelity}` : "",
      item.atmosphere ? `【画面氛围】${item.atmosphere}` : "",
      item.content ? `【完整策略】${item.content}` : "",
    ];
    return lines.filter(Boolean).join("\n");
  }

  function composeOutfitStrategyContent(item) {
    const content = (item.content || "").trim();
    if (content) return content;
    return [item.pose, item.camera, item.fidelity, item.atmosphere].filter(Boolean).join("\n");
  }

  function normalizeOutfitStrategyItems(items) {
    return items.map((item, index) => {
      const scene = findScene(item.id);
      const fidelity =
        item.fidelity ||
        "服装保真约束：保持上传服装的颜色、版型、材质、图案、长度、领口、袖型、廓形和核心外观一致，不换款不改款。";
      return {
        id: item.id || scene.id || `outfit-${index + 1}`,
        name: item.name || scene.label || `场景 ${index + 1}`,
        description: item.description || scene.description || "",
        strategy: item.strategy || scene.strategy || "",
        pose: item.pose || "",
        camera: item.camera || "",
        fidelity,
        atmosphere: item.atmosphere || "",
        content: item.content || [item.pose, item.camera, fidelity, item.atmosphere].filter(Boolean).join("\n"),
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
    const preset = catalog.findOutfitScene(id);
    return {
      id,
      label: preset?.label || id || "服饰穿搭图",
      description: preset?.desc || "",
      strategy: preset?.strategy || getSceneStrategy(id),
    };
  }

  function getSceneName(id) {
    return findScene(id).label;
  }

  function getSceneStrategy(id) {
    return catalog.findOutfitScene(id)?.strategy || "服饰穿搭场景生成";
  }

  function findOutfitStrategyItem(typeId) {
    return outfitStrategyItems.value.find((item) => item.id === typeId) || {
      id: typeId,
      name: getSceneName(typeId),
      content: getSceneStrategy(typeId),
      strategy: getSceneStrategy(typeId),
    };
  }

  onMounted(() => {
    loadCatalog();
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
    workflowStep,
    strategyBrief,
    strategySnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    canGenerateWithStrategy,
    outfitStrategyItems,
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
    canGenerateStrategy,
    selectedCards,
    selectedCardsCount,
    totalCount,
    configuredTotalCount,
    strategyTotalCount,
    selectedImageLabel,
    previewSlides,
    outfitScenes,
    catalogLoading,
    showNotice: toast.info,
    loadOutfitModels,
    uploadModel,
    deleteModel,
    triggerStrategyGeneration,
    confirmStrategyAndGenerate,
    updateOutfitStrategyItem,
    reorderOutfitStrategyItems,
    removeOutfitStrategyItem,
    backToConfig,
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
