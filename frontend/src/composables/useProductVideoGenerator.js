import { computed, onBeforeUnmount, reactive, ref } from "vue";
import { generateVideo, getVideoCreditCosts, getVideoDownloadUrl, getVideoTask } from "@/api/video.js";
import { useAuthStore } from "@/stores/auth.js";
import {
  defaultVideoCreditCosts,
  getVideoDemoType,
  videoDemoTypes,
  videoLanguageOptions,
  videoMarketOptions,
  videoSizeOptions,
} from "@/constants/productVideo.js";

const POLL_INTERVAL_MS = 3000;
const TERMINAL_STATUSES = new Set(["done", "failed", "timeout"]);

function makeId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function getOptionLabel(options, value) {
  return options.find((item) => item.value === value)?.label || value;
}

function getSelectedSize(sizePreset) {
  return videoSizeOptions.find((item) => item.value === sizePreset) || videoSizeOptions[0];
}

function buildSettingsSnapshot(settings) {
  const selectedType = getVideoDemoType(settings.videoType);
  const selectedSize = getSelectedSize(settings.sizePreset);
  return {
    scenario: "product_video",
    type_id: settings.videoType,
    title: selectedType.title,
    input_mode: selectedType.inputMode,
    market: settings.market,
    market_label: getOptionLabel(videoMarketOptions, settings.market),
    language: settings.language,
    language_label: getOptionLabel(videoLanguageOptions, settings.language),
    size_preset: settings.sizePreset,
    aspect_ratio: selectedSize.aspectRatio,
    duration: settings.duration,
    resolution: settings.resolution,
    product_input: settings.productInput,
  };
}

function getRequiredImageMessage(inputMode, count) {
  if (inputMode === "first_frame" && count !== 1) return "请上传 1 张首帧图";
  if (inputMode === "first_last_frame" && count !== 2) return "请上传开始图和结束图";
  if (inputMode === "reference_images" && (count < 1 || count > 9)) {
    return "请上传 1-9 张参考图";
  }
  return "";
}

export function useProductVideoGenerator({ toast } = {}) {
  const authStore = useAuthStore();
  const settings = reactive({
    videoType: videoDemoTypes[0].typeId,
    inputMode: videoDemoTypes[0].inputMode,
    market: "global",
    language: "english",
    sizePreset: "tiktok_9_16",
    duration: 6,
    resolution: "720p",
    productInput: "",
  });
  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);
  const creditCosts = ref({ ...defaultVideoCreditCosts });
  const currentTaskTitle = ref("");
  const outputCards = ref([]);
  const genLogs = ref([]);
  const creatingBatch = ref(false);

  const pollTimers = new Map();
  const pollInFlight = new Set();

  const runningCount = computed(
    () => outputCards.value.filter((card) => !TERMINAL_STATUSES.has(card.status)).length,
  );
  const generatedCount = computed(
    () => outputCards.value.filter((card) => card.status === "done").length,
  );
  const failedCount = computed(
    () =>
      outputCards.value.filter((card) => card.status === "failed" || card.status === "timeout")
        .length,
  );
  const jobTotal = computed(() => outputCards.value.length);
  const generating = computed(() => runningCount.value > 0);
  const selectedCards = computed(() => outputCards.value.filter((card) => card.selected));
  const selectedCardsCount = computed(() => selectedCards.value.length);

  async function loadCreditCosts() {
    try {
      const result = await getVideoCreditCosts();
      if (result.code === 0 && result.data?.costs) {
        creditCosts.value = {
          ...defaultVideoCreditCosts,
          ...result.data.costs,
        };
      }
    } catch {
      toast?.info?.("视频扣费配置读取失败，已使用默认配置");
    }
  }

  function updateSettings(nextSettings) {
    Object.assign(settings, nextSettings);
  }

  function showNotice(message) {
    toast?.info?.(message);
  }

  function createCard({ taskId, typeId, title, settingsSnapshot, creditCost }) {
    return reactive({
      id: makeId(),
      taskId,
      typeId,
      dataUrl: "",
      resultUrl: "",
      selected: false,
      status: "pending",
      strategyTitle: title || "商品视频",
      strategyContent: settingsSnapshot?.product_input || "",
      errorMessage: "",
      sortOrder: outputCards.value.length,
      batchRunId: "",
      creditCost,
      userPrompt: settingsSnapshot?.product_input || "",
      settingsSnapshot,
    });
  }

  async function generateProductVideo() {
    if (generating.value || creatingBatch.value) {
      toast?.info?.("当前视频任务还在生成中");
      return;
    }

    const selectedType = getVideoDemoType(settings.videoType);
    const imageUrls = uploadedImages.value.map((item) => item?.url).filter(Boolean);
    const requirementMessage = getRequiredImageMessage(selectedType.inputMode, imageUrls.length);
    if (requirementMessage) {
      toast?.info?.(requirementMessage);
      return;
    }
    if (uploadedImages.value.some((item) => item?.uploading)) {
      toast?.info?.("素材还在上传中，请稍等");
      return;
    }

    const settingsSnapshot = buildSettingsSnapshot(settings);
    creatingBatch.value = true;
    genLogs.value.push(`[${selectedType.title}] 创建视频任务`);

    try {
      const result = await generateVideo({
        type_id: selectedType.typeId,
        title: selectedType.title,
        input_mode: selectedType.inputMode,
        image_urls: imageUrls,
        user_prompt: settings.productInput,
        duration: settings.duration,
        resolution: settings.resolution,
        aspect_ratio: settingsSnapshot.aspect_ratio,
        settings_snapshot: settingsSnapshot,
        sort_order: outputCards.value.length,
      });

      if (result.code !== 0) {
        toast?.error?.(result.message || "视频任务创建失败");
        return;
      }

      const taskId = result.data?.task_id;
      if (!taskId) {
        toast?.error?.("视频任务创建失败：后端未返回任务 ID");
        return;
      }

      const card = createCard({
        taskId,
        typeId: selectedType.typeId,
        title: selectedType.title,
        settingsSnapshot,
        creditCost: result.data?.credit_cost || 0,
      });
      outputCards.value.unshift(card);
      genLogs.value.push(`[${selectedType.title}] 已进入队列`);
      startPollingCard(card);
    } catch {
      toast?.error?.("视频任务创建失败，请稍后重试");
    } finally {
      creatingBatch.value = false;
    }
  }

  function startPollingCard(card) {
    if (!card.taskId) return;
    stopPollingCard(card.id);
    const timer = window.setInterval(() => {
      pollCardOnce(card).catch(() => {});
    }, POLL_INTERVAL_MS);
    pollTimers.set(card.id, timer);
    pollCardOnce(card).catch(() => {});
  }

  async function pollCardOnce(card) {
    if (!card.taskId || TERMINAL_STATUSES.has(card.status)) {
      stopPollingCard(card.id);
      return;
    }
    if (pollInFlight.has(card.id)) return;
    pollInFlight.add(card.id);
    try {
      const result = await getVideoTask(card.taskId);
      if (result.code !== 0) return;
      const data = result.data || {};
      const status = data.status || "processing";
      const resultUrl = data.result_url || "";

      if (data.settings_snapshot) {
        card.settingsSnapshot = {
          ...(card.settingsSnapshot || {}),
          ...data.settings_snapshot,
        };
      }
      if (typeof data.user_prompt === "string") {
        card.userPrompt = data.user_prompt;
      }
      if (typeof data.progress === "number") {
        card.progress = data.progress;
      }

      if (status === "done" && resultUrl) {
        stopPollingCard(card.id);
        card.resultUrl = resultUrl;
        card.dataUrl = resultUrl;
        card.status = "done";
        card.progress = 100;
        genLogs.value.push(`[${card.strategyTitle}] 已完成`);
        toast?.success?.("商品视频生成完成");
      } else if (status === "failed" || status === "timeout") {
        stopPollingCard(card.id);
        card.status = status;
        card.errorMessage = data.error_message || (status === "timeout" ? "视频生成超时" : "视频生成失败");
        genLogs.value.push(`[${card.strategyTitle}] ${status === "timeout" ? "超时" : "失败"}：${card.errorMessage}`);
        toast?.error?.(card.errorMessage);
      } else {
        card.status = status === "done" ? "processing" : status;
      }
    } catch {
      // 单次轮询失败不打断任务。
    } finally {
      pollInFlight.delete(card.id);
    }
  }

  function stopPollingCard(cardId) {
    const timer = pollTimers.get(cardId);
    if (timer) {
      window.clearInterval(timer);
      pollTimers.delete(cardId);
    }
  }

  function clearAllPollTimers() {
    for (const timer of pollTimers.values()) {
      window.clearInterval(timer);
    }
    pollTimers.clear();
    pollInFlight.clear();
  }

  function toggleCardSelection(id) {
    const card = outputCards.value.find((item) => item.id === id);
    if (card) card.selected = !card.selected;
  }

  function toggleSelectAllCards(value) {
    outputCards.value.forEach((card) => {
      card.selected = value;
    });
  }

  async function downloadSingleVideo(card) {
    if (!card?.taskId || card.status !== "done") {
      toast?.info?.("该视频还未生成完成");
      return;
    }
    try {
      const res = await fetch(getVideoDownloadUrl(card.taskId), {
        headers: { Authorization: `Bearer ${authStore.token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const ext = blob.type === "video/webm" ? "webm" : blob.type === "video/quicktime" ? "mov" : "mp4";
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${currentTaskTitle.value || "商品视频"}_${card.strategyTitle || "video"}.${ext}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      const link = document.createElement("a");
      link.href = card.dataUrl;
      link.target = "_blank";
      link.rel = "noopener";
      link.click();
    }
  }

  async function batchDownload() {
    const downloadable = selectedCards.value.filter(
      (card) => card.status === "done" && card.dataUrl,
    );
    if (downloadable.length === 0) {
      toast?.info?.("请先勾选已生成完成的视频");
      return;
    }
    if (downloadable.length > 1) {
      toast?.info?.("视频批量打包会在资产库接入后开放，当前请单个下载");
      return;
    }
    await downloadSingleVideo(downloadable[0]);
  }

  function removeCard(card) {
    outputCards.value = outputCards.value.filter((item) => item.id !== card.id);
    stopPollingCard(card.id);
  }

  function getVideoModuleName(typeId) {
    return getVideoDemoType(typeId).title || "商品视频";
  }

  onBeforeUnmount(clearAllPollTimers);

  return {
    settings,
    uploadedImages,
    mainImageIndex,
    creditCosts,
    currentTaskTitle,
    outputCards,
    genLogs,
    creatingBatch,
    generating,
    runningCount,
    generatedCount,
    failedCount,
    jobTotal,
    selectedCardsCount,
    loadCreditCosts,
    updateSettings,
    showNotice,
    generateProductVideo,
    toggleCardSelection,
    toggleSelectAllCards,
    downloadSingleVideo,
    batchDownload,
    removeCard,
    getVideoModuleName,
    authStore,
  };
}
