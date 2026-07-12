import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  createDefaultGenerationSettings,
  formatImageLabel,
} from "@/constants/generator.js";
import { outfitPreviewSlides } from "@/constants/outfit.js";
import { generateImageStrategy } from "@/api/image.js";
import { useCardActions } from "@/composables/useCardActions.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/generator/useGenerationCards.js";
import { useMediaBatchRunner } from "@/composables/generator/batch/useMediaBatchRunner.js";
import { useGenerationStrategyFlow } from "@/composables/generator/strategy/useGenerationStrategyFlow.js";
import { useOutfitModels } from "@/composables/outfit/useOutfitModels.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import {
  cloneGenerationSettingsSnapshot,
  cloneUploadedImages,
  createGenerationSettingsSnapshot,
  getSnapshotScene,
  restoreImageGenerationSettings,
  syncImageQuality,
} from "@/utils/generationSnapshots.js";
import { buildOutfitAnalyzeImages, hasUploadingImages } from "@/utils/analyzeImages.js";
import { useCatalogStore } from "@/stores/catalog.js";

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
  const {
    deleteModel,
    loadOutfitModels,
    modelDeletingId,
    modelLibrary,
    modelUploading,
    modelsLoading,
    restoredModelSnapshot,
    selectedModel,
    selectedModelId,
    uploadModel,
  } = useOutfitModels({ toast });
  const selectedScenes = ref([]);
  const sceneDescription = ref("");
  const settings = reactive(createDefaultGenerationSettings({ ratio: "3:4" }));

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
    runStrategy,
    setStrategyResult,
    resetStrategy,
    setStrategyStep,
    updateStrategyItem: updateOutfitStrategyItem,
    reorderStrategyItems: reorderOutfitStrategyItems,
    removeStrategyItem: removeOutfitStrategyItem,
    backToConfig,
  } = strategyFlow;

  const runner = useMediaBatchRunner({
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
    downloading,
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
    syncImageQuality(settings);
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

  function restoreOutfitJobData(data) {
    let restoredStrategyBrief = "";
    if (data.settings && typeof data.settings === "object") {
      const s = data.settings;
      const scene = getSnapshotScene(s);
      const {
        selectedScenes: nextSelectedScenes,
        sceneDescription: nextSceneDescription,
        selectedModelId: nextSelectedModelId,
        selectedModelName: nextSelectedModelName,
        selectedModelImage: nextSelectedModelImage,
        strategyBrief: nextStrategyBrief,
      } = scene;
      restoredStrategyBrief = typeof nextStrategyBrief === "string" ? nextStrategyBrief : "";
      restoreImageGenerationSettings(settings, s);
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

    const outcome = await runStrategy({
      snapshot: inputSnapshot,
      request: () => generateImageStrategy({
        scenario: inputSnapshot.scenario,
        images: inputSnapshot.images,
        platform: settings.platform,
        language: settings.language,
        scene_description: sceneDescription.value,
        selected_model_name: selectedModel.value.name,
        scene_ids: selectedScenes.value,
      }),
      normalizeResult(data) {
        const items = normalizeOutfitStrategyItems(Array.isArray(data.items) ? data.items : []);
        return {
          brief: data.brief || `${settings.platform} / ${settings.language} / ${selectedImageLabel.value}，已为 ${items.length} 个场景生成可编辑穿搭策略。`,
          items,
        };
      },
      emptyMessage: "AI 未返回有效穿搭策略",
      failureMessage: "穿搭策略生成失败，请稍后重试",
    });
    if (!outcome.ok) {
      toast.error(outcome.error ? getApiErrorMessage(outcome.error, outcome.message) : outcome.message);
      return;
    }
    toast.success("穿搭方案已生成，可编辑后继续出图");
  }

  async function confirmStrategyAndGenerate() {
    if (outfitStrategyItems.value.length === 0) {
      toast.info("请先生成穿搭方案");
      return;
    }
    if (strategyDirty.value) {
      toast.info("配置已变化，请先更新穿搭方案");
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
          strategyContent: item.content || item.strategy,
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
      content: item.content || item.strategy || getSceneStrategy(item.id),
      strategy: item.strategy || getSceneStrategy(item.id),
      index: index + 1,
    }));
  }

  function buildUserPromptForItem(item) {
    const lines = [
      `【拍摄场景】${item.name}`,
      item.content ? `【穿搭方案】${item.content}` : "",
    ];
    return lines.filter(Boolean).join("\n");
  }

  function normalizeOutfitStrategyItems(items) {
    return items.map((item, index) => {
      const scene = findScene(item.id);
      const fidelity =
        item.fidelity ||
        "服装保真约束：保持上传服装的颜色、版型、材质、图案、长度、领口、袖型、廓形和核心外观一致，不换款不改款。";
      const content = [
        item.content,
        item.pose && `模特姿态：${item.pose}`,
        item.camera && `镜头角度：${item.camera}`,
        fidelity,
        item.atmosphere && `画面氛围：${item.atmosphere}`,
      ]
        .filter(Boolean)
        .join("\n");
      return {
        id: item.id || scene.id || `outfit-${index + 1}`,
        name: item.name || scene.label || `场景 ${index + 1}`,
        description: item.description || scene.description || "",
        strategy: item.strategy || scene.strategy || "",
        content,
      };
    });
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
    downloading,
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
