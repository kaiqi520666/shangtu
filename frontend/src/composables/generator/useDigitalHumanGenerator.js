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

const DEFAULT_SETTINGS = {
  script: "",
  motionPrompt: "",
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

function createDefaultSettings() {
  return { ...DEFAULT_SETTINGS };
}

export function useDigitalHumanGenerator({ toast, confirm, onJobCreated } = {}) {
  const settings = reactive(createDefaultSettings());
  const selectedAvatar = ref(null);
  const selectedVoice = ref(null);

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

  const canGenerate = computed(() => {
    if (creatingBatch.value || generating.value) return false;
    if (!selectedAvatar.value?.avatar_id) return false;
    if (!selectedVoice.value?.voice_id) return false;
    return Boolean((settings.script || "").trim());
  });

  const generateButtonText = computed(() => {
    if (creatingBatch.value) return "创建任务中...";
    if (generating.value) return "生成中...";
    return "生成视频";
  });

  const voiceLanguage = computed(() => selectedVoice.value?.language || "");

  function updateSettings(nextSettings) {
    Object.assign(settings, nextSettings);
  }

  function showNotice(message) {
    toast?.info?.(message);
  }

  function buildSettingsSnapshot() {
    return createDigitalHumanSettingsSnapshot({
      avatarId: selectedAvatar.value?.avatar_id || "",
      avatarName: selectedAvatar.value?.name || "",
      avatarPreviewImageUrl: selectedAvatar.value?.preview_image_url || "",
      voiceId: selectedVoice.value?.voice_id || "",
      voiceName: selectedVoice.value?.name || "",
      voiceLanguage: selectedVoice.value?.language || "",
      voicePreviewAudioUrl: selectedVoice.value?.preview_audio_url || "",
      script: settings.script,
      motionPrompt: settings.motionPrompt,
      qualityTier: settings.qualityTier,
      resolution: settings.resolution,
      aspectRatio: settings.aspectRatio,
      voiceSettings: {
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
    if (!selectedVoice.value?.voice_id) {
      toast?.info?.("请先选择系统声音");
      return;
    }
    if (!(settings.script || "").trim()) {
      toast?.info?.("请输入口播文案");
      return;
    }

    const settingsSnapshot = buildSettingsSnapshot();
    const title = (currentTaskTitle.value || "").trim() || "数字人视频";
    const queue = [{ qualityTier: settings.qualityTier }];

    await enqueueMediaBatch({
      queue,
      snapshotPayload: {
        settings: settingsSnapshot,
        input_text: settings.script,
      },
      initialLogs: [`[${title}] 创建数字人任务`, "提交数字人、声音和口播文案..."],
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
          voice_id: selectedVoice.value.voice_id,
          script: settings.script,
          motion_prompt: settings.motionPrompt || null,
          quality_tier: item.qualityTier,
          resolution: settings.resolution,
          aspect_ratio: settings.aspectRatio,
          voice_settings: {
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
      strategyContent: scene.script || "",
      sortOrder,
      batchRunId,
      userPrompt: scene.script || "",
      settingsSnapshot,
    });
    card.progress = 10;
    return card;
  }

  function restoreDigitalHumanJobData(data) {
    const snapshot = data.settings || null;
    const scene = getSnapshotScene(snapshot);
    settings.script = data.input_text || scene.script || "";
    settings.motionPrompt = scene.motionPrompt || "";
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

    selectedVoice.value = scene.voiceId
      ? {
          voice_id: scene.voiceId,
          name: scene.voiceName || scene.voiceId,
          language: scene.voiceLanguage || snapshot?.language || "",
          preview_audio_url: scene.voicePreviewAudioUrl || "",
        }
      : null;
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
