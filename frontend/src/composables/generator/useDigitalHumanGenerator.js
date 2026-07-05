import { computed, onBeforeUnmount, reactive, ref } from "vue";
import {
  createDigitalHumanTask,
  deleteDigitalHumanTask,
  getDigitalHumanDownloadUrl,
  pollDigitalHumanTask,
} from "@/api/digitalHuman.js";
import {
  createBatchFinishedHandler,
  useGenerationCards,
} from "@/composables/generator/useGenerationCards.js";
import { useMediaBatchRunner } from "@/composables/generator/batch/useMediaBatchRunner.js";
import { useCardActions } from "@/composables/useCardActions.js";
import {
  createDigitalHumanSettingsSnapshot,
  getSnapshotScene,
} from "@/utils/generationSnapshots.js";
import { useDigitalHumanPricing } from "@/composables/digital-human/useDigitalHumanPricing.js";

const DEFAULT_SETTINGS = {
  script: "",
  qualityTier: "standard",
  resolution: "720p",
  aspectRatio: "9:16",
  voiceSpeed: 1,
};

const QUALITY_TIER_LABELS = {
  standard: "标准档",
  premium: "高质档",
};

const VIDEO_POLL_INTERVAL_MS = 3000;
const MAX_SCRIPT_CHARS = 1500;
const SCRIPT_CHARS_PER_SECOND = 5;

function createDefaultSettings() {
  return { ...DEFAULT_SETTINGS };
}

function isUploadAudioSelection(selection) {
  return selection?.mode === "upload";
}

function hasSelectedAudio(selection) {
  if (!selection) return false;
  return isUploadAudioSelection(selection)
    ? Boolean(selection.audio_asset_id)
    : Boolean(selection.voice_id);
}

function buildPlatformVoiceSelection(voice) {
  if (!voice?.voice_id) return null;
  return {
    ...voice,
    mode: "platform",
  };
}

function buildUploadAudioSelection(audioAsset) {
  if (!audioAsset?.id && !audioAsset?.audio_asset_id) return null;
  return {
    ...audioAsset,
    mode: "upload",
    audio_asset_id: audioAsset.audio_asset_id || audioAsset.id,
  };
}

export function useDigitalHumanGenerator({ toast, confirm, onJobCreated } = {}) {
  const settings = reactive(createDefaultSettings());
  const selectedAvatar = ref(null);
  const selectedVoice = ref(null);
  const backgroundImages = ref([]);
  const pricing = useDigitalHumanPricing();

  const cards = useGenerationCards({
    getTask: pollDigitalHumanTask,
    pollIntervalMs: VIDEO_POLL_INTERVAL_MS,
    mediaLabel: "视频",
    preloadResult: false,
    getLogPrefix: (card) => card.strategyTitle || getDigitalHumanModuleName(card.typeId),
    onCardDone: (card) => {
      card.progress = 100;
    },
    onBatchFinished: createBatchFinishedHandler({
      genLogs: null,
      toast,
      doneLog: "数字人任务已结束",
      successText: "数字人视频生成完成",
      allFailedText: "数字人视频生成失败，请稍后重试",
      partialFailedText: (failed) => `${failed} 个数字人视频生成失败，其余已完成`,
    }),
  });

  const {
    outputCards,
    genLogs,
    creatingBatch,
    generating,
    runningCount,
    generatedCount,
    failedCount,
    jobTotal,
    stopPollingCard,
  } = cards;

  const runner = useMediaBatchRunner({
    scenario: "digital_human",
    cards,
    toast,
    onJobCreated,
    mediaUnit: "个",
    resetSceneState() {
      Object.assign(settings, createDefaultSettings());
      selectedAvatar.value = null;
      selectedVoice.value = null;
      backgroundImages.value = [];
    },
    applyJobData(data) {
      restoreDigitalHumanJobData(data);
    },
    restoreCard(item) {
      const snapshot = item.settings_snapshot || null;
      const scene = getSnapshotScene(snapshot);
      return cards.restoreCard(item, {
        strategyTitle: item.title || "数字人视频",
        strategyContent: scene.script || item.prompt || "",
        settingsSnapshot: snapshot,
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
    enqueueMediaBatch,
    cleanup,
  } = runner;

  const actions = useCardActions({
    outputCards,
    currentTaskTitle,
    getCardName: (card) => card.strategyTitle || getDigitalHumanModuleName(card.typeId),
    getDownloadUrl: (card) => getDigitalHumanDownloadUrl(card.taskId),
    toast,
    mediaLabel: "视频",
    mediaUnit: "个",
    archiveName: "数字人视频",
  });

  const {
    downloading,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleMedia: downloadSingleVideo,
  } = actions;

  const scriptLength = computed(() => (settings.script || "").replace(/\s+/g, "").length);
  const estimatedDurationSeconds = computed(() =>
    Math.ceil(scriptLength.value / SCRIPT_CHARS_PER_SECOND),
  );
  const scriptExceeded = computed(() => scriptLength.value > MAX_SCRIPT_CHARS);
  const backgroundUploading = computed(() =>
    backgroundImages.value.some((item) => item?.uploading),
  );
  const scriptMetaText = computed(() => {
    const durationText = estimatedDurationSeconds.value > 0 ? `，预计约 ${estimatedDurationSeconds.value} 秒` : "";
    return `已输入 ${scriptLength.value}/${MAX_SCRIPT_CHARS} 字${durationText}`;
  });
  const uploadAudioMode = computed(() => isUploadAudioSelection(selectedVoice.value));

  const canGenerate = computed(() => {
    if (creatingBatch.value || generating.value) return false;
    if (!selectedAvatar.value?.avatar_id) return false;
    if (!hasSelectedAudio(selectedVoice.value)) return false;
    if (backgroundUploading.value) return false;
    if (scriptExceeded.value) return false;
    if (uploadAudioMode.value) return true;
    return Boolean((settings.script || "").trim());
  });

  const generateButtonText = computed(() => {
    if (creatingBatch.value) return "创建任务中...";
    if (generating.value) return "生成中...";
    if (backgroundUploading.value) return "背景图上传中...";
    if (scriptExceeded.value) return "文案超过 5 分钟";
    return "生成视频";
  });

  const voiceLanguage = computed(() =>
    uploadAudioMode.value ? "" : selectedVoice.value?.language || "",
  );

  function updateSettings(nextSettings) {
    Object.assign(settings, nextSettings);
  }

  function showNotice(message) {
    toast?.info?.(message);
  }

  function getBackgroundUrl() {
    return backgroundImages.value[0]?.url || "";
  }

  function buildSettingsSnapshot() {
    const selected = selectedVoice.value;
    return createDigitalHumanSettingsSnapshot({
      avatarId: selectedAvatar.value?.avatar_id || "",
      avatarName: selectedAvatar.value?.name || "",
      avatarPreviewImageUrl: selectedAvatar.value?.preview_image_url || "",
      audioMode: uploadAudioMode.value ? "upload" : "platform",
      voiceId: uploadAudioMode.value ? "" : selected?.voice_id || "",
      voiceName: uploadAudioMode.value ? "" : selected?.name || "",
      voiceLanguage: uploadAudioMode.value ? "" : selected?.language || "",
      voicePreviewAudioUrl: uploadAudioMode.value ? "" : selected?.preview_audio_url || "",
      audioAssetId: uploadAudioMode.value ? selected?.audio_asset_id || "" : "",
      audioName: uploadAudioMode.value ? selected?.name || "" : "",
      audioUrl: uploadAudioMode.value ? selected?.audio_url || "" : "",
      audioDurationSeconds: uploadAudioMode.value ? Number(selected?.duration_seconds || 0) : 0,
      backgroundUrl: getBackgroundUrl(),
      script: uploadAudioMode.value ? "" : settings.script,
      qualityTier: settings.qualityTier,
      resolution: settings.resolution,
      aspectRatio: settings.aspectRatio,
      voiceSettings: uploadAudioMode.value
        ? {}
        : {
            speed: Number(settings.voiceSpeed || 1),
          },
    });
  }

  async function generateDigitalHuman() {
    if (creatingBatch.value || generating.value) {
      toast?.info?.("当前数字人任务还在生成中");
      return;
    }
    if (!selectedAvatar.value?.avatar_id) {
      toast?.info?.("请先选择系统数字人");
      return;
    }
    if (!hasSelectedAudio(selectedVoice.value)) {
      toast?.info?.("请先选择系统声音或上传音频");
      return;
    }
    if (backgroundUploading.value) {
      toast?.info?.("背景图上传中，请稍后再生成");
      return;
    }
    if (!uploadAudioMode.value && !(settings.script || "").trim()) {
      toast?.info?.("请输入口播文案");
      return;
    }
    if (scriptExceeded.value) {
      toast?.info?.("当前最多支持约 5 分钟口播文案，请精简后再生成");
      return;
    }

    const settingsSnapshot = buildSettingsSnapshot();
    const title = (currentTaskTitle.value || "").trim() || "数字人视频";
    const queue = [{ qualityTier: settings.qualityTier }];
    const selected = selectedVoice.value;
    const submitLabel = uploadAudioMode.value ? "提交数字人和上传音频..." : "提交数字人、声音和口播文案...";

    await enqueueMediaBatch({
      queue,
      snapshotPayload: {
        settings: settingsSnapshot,
        input_text: uploadAudioMode.value ? "" : settings.script,
      },
      initialLogs: [`[${title}] 创建数字人任务`, submitLabel],
      repeatLog: `[${title}] 创建数字人任务`,
      buildSettingsSnapshot: () => settingsSnapshot,
      createCard({ item, sortOrder, batchRunId, settingsSnapshot: snapshot }) {
        return createCard({
          typeId: item.qualityTier,
          title,
          settingsSnapshot: snapshot,
          sortOrder,
          batchRunId,
        });
      },
      createTask({ item, card, jobId }) {
        return createDigitalHumanTask({
          job_id: jobId,
          title,
          avatar_id: selectedAvatar.value.avatar_id,
          voice_id: uploadAudioMode.value ? undefined : selected?.voice_id,
          audio_asset_id: uploadAudioMode.value ? selected?.audio_asset_id : undefined,
          script: uploadAudioMode.value ? undefined : settings.script,
          background: getBackgroundUrl()
            ? {
                url: getBackgroundUrl(),
              }
            : null,
          quality_tier: item.qualityTier,
          resolution: settings.resolution,
          aspect_ratio: settings.aspectRatio,
          voice_settings: uploadAudioMode.value
            ? undefined
            : {
                speed: Number(settings.voiceSpeed || 1),
              },
        });
      },
      getCreateLog: () => `[${title}] 已进入队列`,
      getFailLogName: () => title,
      allFailedMessage: "数字人任务创建失败，请稍后重试",
      saveErrorMessage: "保存数字人任务配置失败",
      taskIdMissingMessage: "数字人任务创建失败：后端未返回任务 ID",
      insertCards: "after-success",
      preferCreateErrorAsToast: true,
    });
  }

  function createCard({
    typeId,
    title,
    settingsSnapshot,
    sortOrder = outputCards.value.length,
    batchRunId = "",
  }) {
    const scene = getSnapshotScene(settingsSnapshot);
    const card = cards.createCard({
      typeId,
      strategyTitle: title || "数字人视频",
      strategyContent: scene.script || scene.audioName || "",
      sortOrder,
      batchRunId,
      userPrompt: scene.script || scene.audioName || "",
      settingsSnapshot,
    });
    card.progress = 10;
    return card;
  }

  function restoreDigitalHumanJobData(data) {
    const snapshot = data.settings || null;
    const scene = getSnapshotScene(snapshot);
    settings.script = data.input_text || scene.script || "";
    settings.qualityTier = scene.qualityTier || "standard";
    settings.resolution = scene.resolution || snapshot?.quality || "720p";
    settings.aspectRatio = scene.aspectRatio || snapshot?.ratio || "9:16";
    settings.voiceSpeed = Number(scene.voiceSettings?.speed || 1);

    selectedAvatar.value = scene.avatarId
      ? {
          avatar_id: scene.avatarId,
          name: scene.avatarName || scene.avatarId,
          preview_image_url: scene.avatarPreviewImageUrl || "",
        }
      : null;

    if ((scene.audioMode || "") === "upload" && scene.audioAssetId) {
      selectedVoice.value = buildUploadAudioSelection({
        id: scene.audioAssetId,
        name: scene.audioName || scene.audioAssetId,
        audio_url: scene.audioUrl || "",
        duration_seconds: Number(scene.audioDurationSeconds || 0),
        content_type: "",
        size: 0,
      });
    } else {
      selectedVoice.value = scene.voiceId
        ? buildPlatformVoiceSelection({
            voice_id: scene.voiceId,
            name: scene.voiceName || scene.voiceId,
            language: scene.voiceLanguage || snapshot?.language || "",
            preview_audio_url: scene.voicePreviewAudioUrl || "",
          })
        : null;
    }
    backgroundImages.value = scene.backgroundUrl
      ? [
          {
            id: `background_${scene.backgroundUrl}`,
            previewUrl: scene.backgroundUrl,
            url: scene.backgroundUrl,
            objectKey: "",
            contentType: "",
            size: 0,
            uploading: false,
            error: "",
            source: "asset",
          },
        ]
      : [];
  }

  async function removeCard(card) {
    if (!card?.taskId) {
      outputCards.value = outputCards.value.filter((item) => item.id !== card?.id);
      return;
    }

    const ok = await confirm?.open?.({
      title: "删除视频",
      message: "确定删除这个数字人视频吗？视频不会立即从存储中物理删除。",
      confirmText: "删除",
      cancelText: "取消",
      tone: "danger",
    });
    if (ok === false) return;

    try {
      const result = await deleteDigitalHumanTask(card.taskId);
      if (result.code !== 0) {
        toast?.error?.(result.message || "删除失败");
        return;
      }
      outputCards.value = outputCards.value.filter((item) => item.id !== card.id);
      stopPollingCard(card.id);
      toast?.success?.("视频已删除");
    } catch {
      toast?.error?.("删除失败，请稍后重试");
    }
  }

  function getDigitalHumanModuleName(typeId) {
    return QUALITY_TIER_LABELS[typeId] || "数字人视频";
  }

  onBeforeUnmount(() => {
    cleanup();
  });

  return {
    settings,
    selectedAvatar,
    selectedVoice,
    backgroundImages,
    uploadAudioMode,
    currentJobId,
    currentTaskTitle,
    historyTasks,
    showHistoryDrawer,
    historyLoading,
    jobLoading,
    outputCards,
    genLogs,
    creatingBatch,
    generating,
    runningCount,
    generatedCount,
    failedCount,
    jobTotal,
    downloading,
    selectedCardsCount,
    voiceLanguage,
    qualityOptions: pricing.qualityOptions,
    loadPricing: pricing.loadPricing,
    scriptLength,
    estimatedDurationSeconds,
    scriptExceeded,
    scriptMetaText,
    canGenerate,
    generateButtonText,
    updateSettings,
    showNotice,
    generateDigitalHuman,
    updateCurrentJobTitle,
    createNewTask,
    resetWorkspaceToDraft,
    loadHistoryTasks,
    loadGenerationJob,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleVideo,
    removeCard,
    getDigitalHumanModuleName,
  };
}
