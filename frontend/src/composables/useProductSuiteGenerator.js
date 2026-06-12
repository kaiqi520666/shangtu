import { computed, onBeforeUnmount, reactive, ref } from "vue";
import JSZip from "jszip";
import { ratioOptions, resolutionMap, resolveQuality } from "@/constants/generator.js";
import { suiteStructureDefaults } from "@/constants/productSuite.js";
import { useToast } from "@/composables/useToast.js";
import { analyzeImage, generateImage, getImageDownloadUrl, getImageTask } from "@/api/image.js";
import {
  createGenerationJob,
  getGenerationJob,
  listGenerationJobs,
  updateGenerationJob,
} from "@/api/generation.js";

const POLL_INTERVAL_MS = 5000;
const TERMINAL_STATUSES = new Set(["done", "failed", "timeout"]);
const TITLE_DEBOUNCE_MS = 600;

function preloadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = resolve;
    img.onerror = reject;
    img.src = url;
  });
}

function getToken() {
  try {
    const raw = window.localStorage.getItem("nodepass_auth_user");
    return raw ? JSON.parse(raw)?.token : "";
  } catch {
    return "";
  }
}

export function useProductSuiteGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);
  const aiLoading = ref(false);
  const generating = ref(false);
  const generatedCount = ref(0);
  const jobTotal = ref(0);
  const genLogs = ref([]);
  const outputCards = ref([]);
  const zoomCard = ref(null);
  const currentJobId = ref("");
  const currentTaskTitle = ref("");
  const historyTasks = ref([]);
  const showHistoryDrawer = ref(false);
  const historyLoading = ref(false);
  const jobLoading = ref(false);
  const activeBatchRunId = ref("");

  const pollTimers = new Map();
  const pollInFlight = new Set();

  const settings = reactive({
    platform: "亚马逊",
    language: "中文",
    ratio: "1:1",
    quality: "1K",
    productInput: "",
  });

  const suiteStructure = ref(
    suiteStructureDefaults.map((item) => ({
      ...item,
      enabled: true,
      count: item.defaultCount,
    })),
  );

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
  const selectedCards = computed(() => outputCards.value.filter((card) => card.selected));
  const selectedCardsCount = computed(() => selectedCards.value.length);
  const selectedRatioOption = computed(
    () => ratioOptions.find((option) => option.value === settings.ratio) || ratioOptions[0],
  );
  const selectedImageLabel = computed(() => {
    const { width, height } = getCardSize();
    return `${settings.quality} / ${selectedRatioOption.value.label} / ${width}x${height}`;
  });

  let titleDebounceTimer = null;

  function updateCurrentJobTitle(title) {
    const trimmed = (title || "").trim();
    currentTaskTitle.value = title; // 保留用户输入（含未 trim 的空格）
    if (!currentJobId.value) return;
    if (!trimmed) return; // 空标题不提交

    if (titleDebounceTimer) {
      clearTimeout(titleDebounceTimer);
    }
    titleDebounceTimer = setTimeout(async () => {
      try {
        const res = await updateGenerationJob(currentJobId.value, { title: trimmed });
        if (res.code !== 0) {
          toast.error("任务标题保存失败");
        }
      } catch {
        toast.error("任务标题保存失败");
      }
    }, TITLE_DEBOUNCE_MS);
  }

  async function ensureCurrentJob() {
    if (currentJobId.value) return currentJobId.value;
    try {
      const result = await createGenerationJob("product_suite");
      if (result.code !== 0) {
        toast.error(result.message || "创建任务失败");
        return "";
      }
      currentJobId.value = result.data.job_id;
      currentTaskTitle.value = result.data.title;
      onJobCreated?.(currentJobId.value);
      return currentJobId.value;
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "创建任务失败");
      }
      return "";
    }
  }

  async function createNewTask() {
    if (generating.value) {
      toast.info("当前任务正在生成中，请稍后再新建任务");
      return false;
    }
    clearAllPollTimers();
    resetWorkspaceToDraft();
    return true;
  }

  function resetWorkspaceToDraft() {
    clearAllPollTimers();
    uploadedImages.value = [];
    mainImageIndex.value = 0;
    settings.productInput = "";
    outputCards.value = [];
    genLogs.value = [];
    generatedCount.value = 0;
    jobTotal.value = 0;
    activeBatchRunId.value = "";
    currentJobId.value = "";
    currentTaskTitle.value = "";
    suiteStructure.value = suiteStructureDefaults.map((item) => ({
      ...item,
      enabled: true,
      count: item.defaultCount,
    }));
  }

  async function loadHistoryTasks() {
    historyLoading.value = true;
    try {
      const result = await listGenerationJobs("product_suite");
      if (result.code !== 0) {
        toast.error(result.message || "加载历史任务失败");
        historyTasks.value = [];
        return;
      }
      historyTasks.value = result.data || [];
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "加载历史任务失败");
      }
      historyTasks.value = [];
    } finally {
      historyLoading.value = false;
    }
  }

  async function loadGenerationJob(jobId) {
    if (!jobId) return false;
    if (generating.value) {
      toast.info("当前任务正在生成中，请稍后再切换任务");
      return false;
    }
    jobLoading.value = true;
    try {
      const result = await getGenerationJob(jobId);
      if (result.code !== 0) {
        toast.error(result.message || "任务不存在或无权限访问");
        return false;
      }
      const data = result.data || {};
      clearAllPollTimers();
      currentJobId.value = data.job_id;
      currentTaskTitle.value = data.title || "";
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
        suiteStructure.value = suiteStructureDefaults.map((item) => ({
          ...item,
          enabled: true,
          count: item.defaultCount,
        }));
      }

      const items = Array.isArray(data.items) ? data.items : [];
      const restoredCards = items.map((item) =>
        reactive({
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
        }),
      );
      outputCards.value = restoredCards;

      const pendingCards = restoredCards.filter((card) => !TERMINAL_STATUSES.has(card.status));
      const doneCount = restoredCards.filter((card) => card.status === "done").length;
      generatedCount.value = doneCount;
      jobTotal.value = restoredCards.length;
      genLogs.value = restoredCards.length
        ? [`已恢复任务「${currentTaskTitle.value}」，共 ${restoredCards.length} 张`]
        : [];

      if (pendingCards.length > 0) {
        generating.value = true;
        const resumeBatchId = makeId();
        activeBatchRunId.value = resumeBatchId;
        pendingCards.forEach((card) => {
          card.batchRunId = resumeBatchId;
          startPollingCard(card);
        });
      } else {
        generating.value = false;
      }
      return true;
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "任务不存在或无权限访问");
      }
      return false;
    } finally {
      jobLoading.value = false;
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

    const jobId = await ensureCurrentJob();
    if (!jobId) return;

    const snapshotPayload = {
      title: currentTaskTitle.value,
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
    try {
      const saveRes = await updateGenerationJob(jobId, snapshotPayload);
      if (saveRes.code !== 0) {
        toast.error(saveRes.message || "保存任务配置失败，请稍后重试");
        return;
      }
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "保存任务配置失败，请稍后重试");
      }
      return;
    }

    generating.value = true;
    generatedCount.value = 0;
    jobTotal.value = queue.length;
    const baseSortOrder = outputCards.value.length;
    const batchRunId = makeId();
    activeBatchRunId.value = batchRunId;
    if (genLogs.value.length === 0) {
      genLogs.value.push("商品套图生成任务初始化...", "读取商品图片、平台规范与套图结构...");
    } else {
      genLogs.value.push(`新一批套图开始生成，共 ${queue.length} 张`);
    }

    const imageUrl = mainImg.url;

    const createdCards = [];

    queue.forEach((item, index) => {
      const card = reactive({
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
        sortOrder: baseSortOrder + index,
        batchRunId,
        creditRefunded: false,
      });
      createdCards.push({ card, item });
    });

    // 新批次插到前面，让最新生成更醒目；旧 cards 保留
    outputCards.value = [...createdCards.map((c) => c.card), ...outputCards.value];

    let successfullyEnqueued = 0;
    for (const { card, item } of createdCards) {
      const prompt = buildPromptForItem(item);
      try {
        const result = await generateImage({
          prompt,
          image_url: imageUrl,
          ratio: settings.ratio,
          resolution: settings.quality,
          job_id: jobId,
          type_id: item.id,
          title: card.strategyTitle,
          sort_order: card.sortOrder,
        });
        if (result.code !== 0) {
          card.status = "failed";
          card.errorMessage = result.message || "任务创建失败";
          genLogs.value.push(`[${item.name} ${item.index}] 创建失败：${card.errorMessage}`);
          continue;
        }
        card.taskId = result.data.task_id;
        genLogs.value.push(`正在生成 [${item.name}] 第 ${item.index} 张...`);
        startPollingCard(card);
        successfullyEnqueued += 1;
      } catch (error) {
        const status = error.response?.status;
        const message =
          status === 401
            ? "登录已过期，请重新登录"
            : error.response?.data?.message || "任务创建失败";
        card.status = "failed";
        card.errorMessage = message;
        genLogs.value.push(`[${item.name} ${item.index}] 创建失败：${message}`);
      }
    }

    genLogs.value.push(`已创建 ${successfullyEnqueued} 个商品套图任务`);
    if (successfullyEnqueued === 0) {
      maybeFinishGenerating();
      if (generating.value) {
        generating.value = false;
      }
      jobTotal.value = 0;
      toast.error("所有套图任务都创建失败，请稍后重试");
    }
  }

  function buildPromptForItem(item) {
    const lines = [
      "【参考图】必须以用户上传的商品图为商品主体，保持商品款式、颜色、材质、结构和外观完全一致。",
      `【投放平台】${settings.platform}`,
      `【排版语言】${settings.language}`,
      `【画面比例】${settings.ratio}`,
      `【图类型】${item.name}`,
      `【图类型说明】${item.description}`,
      "【商品卖点与要求】",
      settings.productInput.trim(),
      "【强约束】禁止虚构品牌 Logo、认证标识、价格、销量、参数等无法从参考图与上述卖点确认的信息；如需添加文字必须使用上述指定语言，文字简洁清晰，适合电商平台展示。",
    ];
    return lines.filter(Boolean).join("\n");
  }

  function startPollingCard(card) {
    if (!card.taskId) return;
    // 避免重复 timer（重新生成场景）
    stopPollingCard(card.id);
    const timer = window.setInterval(() => {
      pollCardOnce(card).catch(() => {});
    }, POLL_INTERVAL_MS);
    pollTimers.set(card.id, timer);
    pollCardOnce(card).catch(() => {});
  }

  async function pollCardOnce(card) {
    if (!card.taskId) return;
    if (TERMINAL_STATUSES.has(card.status)) {
      stopPollingCard(card.id);
      return;
    }
    if (pollInFlight.has(card.id)) return;
    pollInFlight.add(card.id);
    try {
      const result = await getImageTask(card.taskId);
      if (result.code !== 0) {
        return;
      }
      // 处理本次响应前再校验一次终态，避免并发响应叠加导致 generatedCount 重复 +1
      if (TERMINAL_STATUSES.has(card.status)) {
        stopPollingCard(card.id);
        return;
      }
      const data = result.data || {};
      const status = data.status || "processing";
      const resultUrl = data.result_url || "";

      if (status === "done" && resultUrl) {
        // 防御：重新生成场景下，如果返回的 resultUrl 跟旧图一样，说明后端还没拿到新图
        if (card.previousResultUrl && resultUrl === card.previousResultUrl) {
          // 继续轮询，不停止
          card.status = "processing";
        } else {
          // 先停轮询，避免重复处理
          stopPollingCard(card.id);
          // 保持遮罩：预加载新图完成后再切换状态
          try {
            await preloadImage(resultUrl);
          } catch {
            // 预加载失败也继续，浏览器会用 img src 正常请求
          }
          card.resultUrl = resultUrl;
          card.dataUrl = resultUrl;
          card.previousResultUrl = "";
          card.status = "done";
          generatedCount.value += 1;
          genLogs.value.push(`[${card.strategyTitle}] 已完成`);
          genLogs.value.push(`已完成 ${generatedCount.value}/${jobTotal.value}`);
        }
      } else if (status === "failed" || status === "timeout") {
        card.status = status;
        card.errorMessage = data.error_message || (status === "timeout" ? "生成超时" : "生成失败");
        genLogs.value.push(
          `[${card.strategyTitle}] ${status === "timeout" ? "超时" : "失败"}：${card.errorMessage}`,
        );
        stopPollingCard(card.id);
      } else {
        // 包含两种情况：1) processing；2) done 但 result_url 仍未落库（worker 写入竞态/降级）
        card.status = status === "done" ? "processing" : status;
      }

      maybeFinishGenerating();
    } catch {
      // 单次轮询异常不停止该任务，等下一次 tick；网络抖动等场景靠后端最终态收敛
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

  function maybeFinishGenerating() {
    if (!generating.value) return;
    const batchId = activeBatchRunId.value;
    const batchCards = batchId
      ? outputCards.value.filter((card) => card.batchRunId === batchId)
      : outputCards.value;
    if (batchCards.length === 0) return;
    const allTerminal = batchCards.every((card) => TERMINAL_STATUSES.has(card.status));
    if (allTerminal) {
      generating.value = false;
      genLogs.value.push("全部商品套图任务已结束");
      const failedCount = batchCards.filter((card) => card.status !== "done").length;
      if (failedCount === 0) {
        toast.success("商品套图已全部生成");
      } else if (failedCount === batchCards.length) {
        toast.error("套图生成失败，请稍后重试");
      } else {
        toast.info(`部分套图生成失败（${failedCount} 张）`);
      }
    }
  }

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

  function toggleCardSelection(id) {
    const card = outputCards.value.find((item) => item.id === id);
    if (card) card.selected = !card.selected;
  }

  function toggleSelectAllCards(value) {
    outputCards.value.forEach((card) => {
      card.selected = value;
    });
  }

  function batchDownload() {
    const downloadable = selectedCards.value.filter(
      (card) => card.status === "done" && card.dataUrl,
    );
    if (downloadable.length === 0) {
      toast.info("请先勾选已生成完成的套图");
      return;
    }

    if (downloadable.length === 1) {
      downloadSingleImage(downloadable[0]);
      return;
    }

    // 多张打 zip 包下载
    downloadAsZip(downloadable);
  }

  async function downloadAsZip(cards) {
    toast.info(`正在打包 ${cards.length} 张图片...`);
    const zip = new JSZip();
    const token = getToken();

    const results = await Promise.allSettled(
      cards.map(async (card, index) => {
        const url = getImageDownloadUrl(card.taskId);
        const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        const ext = blob.type === "image/jpeg" ? "jpg" : "png";
        const name = `${card.strategyTitle || getStructureName(card.typeId)}_${index + 1}.${ext}`;
        zip.file(name, blob);
      }),
    );

    const succeeded = results.filter((r) => r.status === "fulfilled").length;
    if (succeeded === 0) {
      toast.error("图片下载失败，请稍后重试");
      return;
    }

    try {
      const content = await zip.generateAsync({ type: "blob" });
      const url = URL.createObjectURL(content);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${currentTaskTitle.value || "商品套图"}.zip`;
      link.click();
      URL.revokeObjectURL(url);
      if (succeeded < cards.length) {
        toast.info(`已打包 ${succeeded}/${cards.length} 张，部分图片下载失败`);
      } else {
        toast.success("打包下载完成");
      }
    } catch {
      toast.error("打包失败，请稍后重试");
    }
  }

  async function downloadSingleImage(card) {
    if (!card.dataUrl) {
      toast.info("该套图还未生成完成");
      return;
    }
    try {
      const url = getImageDownloadUrl(card.taskId);
      const token = getToken();
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const ext = blob.type === "image/jpeg" ? "jpg" : "png";
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `${currentTaskTitle.value}_${card.strategyTitle || getStructureName(card.typeId)}.${ext}`;
      link.click();
      URL.revokeObjectURL(blobUrl);
    } catch {
      // fallback 到直接打开
      const link = document.createElement("a");
      link.href = card.dataUrl;
      link.target = "_blank";
      link.rel = "noopener";
      link.click();
    }
  }

  function regenerateSingleCard(_card) {
    toast.info("请点击编辑图片按钮进行重新生成");
  }

  onBeforeUnmount(() => {
    clearAllPollTimers();
    if (titleDebounceTimer) {
      clearTimeout(titleDebounceTimer);
      titleDebounceTimer = null;
    }
  });

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

function makeId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
