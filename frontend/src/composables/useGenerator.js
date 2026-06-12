import { computed, reactive, ref } from "vue";
import { availableModules, ratioOptions, resolutionMap, resolveQuality } from "@/constants/generator.js";
import { useToast } from "@/composables/useToast.js";
import { analyzeImage } from "@/api/image.js";

const THEME_COLORS = {
  primary: "#10b981",
  primaryDark: "#059669",
  slate900: "#0f172a",
  slate600: "#475569",
  slate500: "#64748b",
  slate100: "#f1f5f9",
};

export function useGenerator() {
  const toast = useToast();
  const uploadedImages = ref([]);
  const mainImageIndex = ref(0);
  const selectedModules = ref([
    "first-screen",
    "core-selling",
    "use-scenario",
    "multi-angle",
    "detail-zoom",
    "ambient-scene",
  ]);
  const currentTaskTitle = ref(
    `Task_${new Date().toISOString().slice(0, 10).replace(/-/g, "")}_商品主图批量生成`,
  );
  const generating = ref(false);
  const generatedCount = ref(0);
  const genLogs = ref([]);
  const outputCards = ref([]);
  const showHistoryDrawer = ref(false);
  const showQueueDrawer = ref(false);
  const showLongPreviewModal = ref(false);
  const zoomCard = ref(null);
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

  // TODO: replace with API
  const taskQueue = ref([]);

  // TODO: replace with API
  const historyTasks = ref([]);

  const strategyLoading = computed(() => workflowStep.value === "strategy-loading");
  const strategyPanelVisible = computed(
    () => workflowStep.value === "strategy-loading" || workflowStep.value === "strategy-review",
  );
  const hasGenerationSource = computed(
    () => uploadedImages.value.length > 0 && settings.productInput.trim().length > 0,
  );
  const canGenerate = computed(
    () =>
      hasGenerationSource.value &&
      selectedModules.value.length > 0 &&
      !generating.value &&
      !strategyLoading.value,
  );
  const selectedCards = computed(() => outputCards.value.filter((card) => card.selected));
  const selectedCardsCount = computed(() => selectedCards.value.length);
  const generationProgressClass = computed(() =>
    getProgressWidthClass((generatedCount.value / Math.max(selectedModules.value.length, 1)) * 100),
  );
  const selectedRatioOption = computed(
    () => ratioOptions.find((option) => option.value === settings.ratio) || ratioOptions[0],
  );
  const selectedImageLabel = computed(() => {
    const { width, height } = getCardSize();
    return `${settings.quality} / ${selectedRatioOption.value.label} / ${width}x${height}`;
  });
  const longPreviewHeight = computed(() => {
    const { height } = getCardSize();
    return selectedCardsCount.value * height;
  });

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

  function getModuleName(id) {
    return availableModules.find((module) => module.id === id)?.name || id;
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

  async function triggerStrategyGeneration() {
    if (!hasGenerationSource.value) {
      toast.info("请先上传产品图并填写商品卖点与要求");
      return;
    }

    if (selectedModules.value.length === 0) {
      toast.info("请至少选择一个生成图种");
      return;
    }

    workflowStep.value = "strategy-loading";
    strategyBrief.value = "";
    moduleContents.value = [];
    outputCards.value = [];
    generatedCount.value = 0;

    await wait(800);

    const productName = getProductNameFromInput(settings.productInput);
    const moduleMap = new Map(availableModules.map((module) => [module.id, module]));

    // TODO: replace with API
    moduleContents.value = selectedModules.value
      .map((moduleId, index) => {
        const module = moduleMap.get(moduleId);
        if (!module) return null;

        return {
          id: module.id,
          moduleName: module.name,
          title: buildModuleTitle(module, productName),
          content: buildModuleContent(module, index),
          strategy: module.strategy,
        };
      })
      .filter(Boolean);

    strategyBrief.value = `${settings.platform} / ${settings.language} / ${selectedImageLabel.value}，已为 ${moduleContents.value.length} 个图种生成可编辑模块内容。`;
    workflowStep.value = "strategy-review";
    toast.success("模块策略已生成，可编辑后继续出图");
  }

  async function confirmStrategyAndGenerate() {
    if (moduleContents.value.length === 0) {
      toast.info("请先生成模块策略");
      return;
    }

    await triggerBatchGeneration();
  }

  async function triggerBatchGeneration() {
    if (uploadedImages.value.length === 0) {
      toast.info("请先上传产品图");
      return;
    }

    const moduleQueue = moduleContents.value.length
      ? moduleContents.value
      : selectedModules.value.map((moduleId) => ({
          id: moduleId,
          moduleName: getModuleName(moduleId),
          title: getModuleName(moduleId),
          content: getModuleStrategy(moduleId),
          strategy: getModuleStrategy(moduleId),
        }));

    if (moduleQueue.length === 0) {
      toast.info("请至少选择一个生成图种");
      return;
    }

    workflowStep.value = "image-generating";
    generating.value = true;
    generatedCount.value = 0;
    genLogs.value = ["AI 排版渲染管道初始化成功...", "读取您的平台、语言与尺寸偏好..."];
    outputCards.value = [];

    const mainImg = uploadedImages.value[mainImageIndex.value];

    for (const moduleItem of moduleQueue) {
      await wait(180);
      genLogs.value.push(`正在为 [${moduleItem.moduleName}] 执行多层级渲染绘制...`);
      const base64 = await renderCardImage(moduleItem.id, getImageSrc(mainImg), moduleItem);
      outputCards.value.push({
        id: makeCardId(),
        typeId: moduleItem.id,
        strategyTitle: moduleItem.title,
        strategyContent: moduleItem.content,
        dataUrl: base64,
        selected: true,
      });
      generatedCount.value += 1;
    }

    genLogs.value.push("批量渲染生成任务全部完成，数据已同步至主工作区。");
    generating.value = false;

    historyTasks.value.unshift({
      id: makeCardId(),
      title: currentTaskTitle.value,
      platform: settings.platform,
      time: new Date().toLocaleTimeString(),
      cardsCount: outputCards.value.length,
      cards: JSON.parse(JSON.stringify(outputCards.value)),
    });
    workflowStep.value = "result";
    toast.success("批量渲染生成任务已完成");
  }

  function renderCardImage(typeId, productImgSrc, moduleItem = null) {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      const { width, height } = getCardSize();

      canvas.width = width;
      canvas.height = height;
      paintBackground(ctx, width, height);

      const img = new window.Image();
      img.onload = () => {
        paintProduct(ctx, img, typeId, width, height);
        applyStrategyDecorations(ctx, typeId, width, height, moduleItem);
        resolve(canvas.toDataURL("image/png"));
      };
      img.onerror = reject;
      img.src = productImgSrc;
    });
  }

  function paintBackground(ctx, width, height) {
    const bgGrad = ctx.createLinearGradient(0, 0, width, height);
    if (["亚马逊", "Wayfair", "Coupang"].includes(settings.platform)) {
      bgGrad.addColorStop(0, "#f8fafc");
      bgGrad.addColorStop(1, "#e2e8f0");
    } else if (["Shopee", "Temu", "TikTok Shop", "SHEIN"].includes(settings.platform)) {
      bgGrad.addColorStop(0, "#fffbeb");
      bgGrad.addColorStop(1, "#ffedd5");
    } else {
      bgGrad.addColorStop(0, "#ffffff");
      bgGrad.addColorStop(1, THEME_COLORS.slate100);
    }

    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(16, 185, 129, 0.05)";
    ctx.lineWidth = 1;

    for (let x = 0; x < width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  }

  function paintProduct(ctx, img, typeId, width, height) {
    let productX = width / 2;
    let productY = height / 2 + 50;
    let productW = width * 0.65;
    let productH = height * 0.65;

    if (typeId === "first-screen") {
      productW = width * 0.75;
      productH = height * 0.75;
    } else if (typeId === "core-selling" || typeId === "tech-specs") {
      productX = width * 0.72;
      productY = height * 0.62;
      productW = width * 0.48;
      productH = height * 0.48;
    } else if (typeId === "detail-zoom") {
      productX = width * 0.35;
      productY = height * 0.58;
      productW = width * 0.55;
    }

    ctx.shadowColor = "rgba(15, 23, 42, 0.08)";
    ctx.shadowBlur = 24;
    ctx.shadowOffsetY = 12;
    ctx.drawImage(img, productX - productW / 2, productY - productH / 2, productW, productH);
    ctx.shadowColor = "transparent";
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
  }

  function applyStrategyDecorations(ctx, typeId, width, height, moduleItem = null) {
    const inputLines = settings.productInput
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    const strategyLines = parseStrategyLines(moduleItem?.content || "");
    const mainTitle = moduleItem?.title || inputLines[0] || "NodePass AI 爆款推荐";
    let bulletPoints = strategyLines.length ? strategyLines : inputLines.slice(1);

    if (bulletPoints.length === 0) {
      bulletPoints = [
        "1. 突破技术瓶颈 / 首发体验",
        "2. 高精美学结构 / 触手可及",
        "3. 尊享官方售后 / 闪电发货",
      ];
    }

    paintHeroDecorations(ctx, typeId, width, mainTitle);
    paintCoreSelling(ctx, typeId, height, bulletPoints);
    paintSpecs(ctx, typeId, height, mainTitle);
    paintWarranty(ctx, typeId, width, height);
    paintDetailZoom(ctx, typeId, width, height);
    paintPlatformBadge(ctx, width);
  }

  function paintHeroDecorations(ctx, typeId, width, mainTitle) {
    if (typeId !== "first-screen" && typeId !== "brand-story") return;

    ctx.fillStyle = "rgba(16, 185, 129, 0.06)";
    ctx.fillRect(40, 40, width - 80, 160);
    ctx.strokeStyle = "rgba(16, 185, 129, 0.15)";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(40, 40, width - 80, 160);
    ctx.fillStyle = THEME_COLORS.slate900;
    ctx.font = 'bold 32px "Noto Sans SC", sans-serif';
    ctx.fillText(mainTitle.slice(0, 20), 60, 95);

    if (["抖音电商", "淘宝天猫1688", "拼多多", "京东"].includes(settings.platform)) {
      ctx.fillStyle = THEME_COLORS.primary;
      ctx.beginPath();
      ctx.roundRect(60, 120, 150, 32, 6);
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = 'bold 16px "Noto Sans SC", sans-serif';
      ctx.fillText("限时特惠首发", 78, 142);
    } else {
      ctx.fillStyle = THEME_COLORS.slate600;
      ctx.font = '15px "Plus Jakarta Sans", sans-serif';
      ctx.fillText("NEW ARRIVAL / 2026 EDITION", 60, 140);
    }

    ctx.fillStyle = "rgba(16, 185, 129, 0.15)";
    ctx.font = 'italic bold 54px "Plus Jakarta Sans", sans-serif';
    ctx.fillText("PREMIUM", width - 310, 150);
  }

  function paintCoreSelling(ctx, typeId, height, bulletPoints) {
    if (typeId !== "core-selling") return;

    ctx.fillStyle = "rgba(255, 255, 255, 0.98)";
    ctx.beginPath();
    ctx.roundRect(40, 40, 380, height - 80, 16);
    ctx.fill();
    ctx.strokeStyle = "rgba(16, 185, 129, 0.2)";
    ctx.stroke();
    ctx.fillStyle = THEME_COLORS.primaryDark;
    ctx.font = 'bold 16px "Noto Sans SC", sans-serif';
    ctx.fillText("KEY FEATURES / 核心优势", 60, 80);

    let yOffset = 130;
    bulletPoints.slice(0, 6).forEach((point, index) => {
      ctx.fillStyle = THEME_COLORS.primary;
      ctx.beginPath();
      ctx.arc(70, yOffset, 12, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = 'bold 14px "Plus Jakarta Sans", sans-serif';
      ctx.fillText(index + 1, 66, yOffset + 5);

      const cleanText = point.replace(/^\d+[.、]/, "").trim();
      const parts = cleanText.split("/");
      ctx.fillStyle = THEME_COLORS.slate900;
      ctx.font = 'bold 16px "Noto Sans SC", sans-serif';
      ctx.fillText(parts[0] || "", 95, yOffset - 5);
      if (parts[1]) {
        ctx.fillStyle = "#4b5563";
        ctx.font = '13px "Noto Sans SC", sans-serif';
        ctx.fillText(parts[1], 95, yOffset + 15);
      }
      yOffset += 85;
    });

    ctx.strokeStyle = "rgba(0,0,0,0.06)";
    ctx.beginPath();
    ctx.moveTo(60, yOffset);
    ctx.lineTo(380, yOffset);
    ctx.stroke();
    ctx.fillStyle = THEME_COLORS.slate500;
    ctx.font = '12px "Plus Jakarta Sans", sans-serif';
    ctx.fillText("NODEPASS AI DESIGN SYSTEM", 60, yOffset + 30);
  }

  function paintSpecs(ctx, typeId, height, mainTitle) {
    if (typeId !== "tech-specs") return;

    ctx.fillStyle = "rgba(255, 255, 255, 0.98)";
    ctx.beginPath();
    ctx.roundRect(40, 40, 380, height - 80, 16);
    ctx.fill();
    ctx.strokeStyle = "rgba(16, 185, 129, 0.15)";
    ctx.stroke();
    ctx.fillStyle = THEME_COLORS.primaryDark;
    ctx.font = 'bold 16px "Noto Sans SC", sans-serif';
    ctx.fillText("DETAILED PARAMETERS / 规格配置", 60, 80);

    const specs = [
      { label: "商品名称", val: mainTitle.slice(0, 10) },
      { label: "安全标准", val: "符合3C国际安全准则" },
      { label: "核心功效", val: "全速增效、降躁隔离" },
      { label: "质保政策", val: "1年超长保修、顺丰寄回" },
      { label: "包装配件", val: "主机、充电线、多尺寸套" },
    ];

    let rowY = 130;
    specs.forEach((spec) => {
      ctx.fillStyle = "rgba(16, 185, 129, 0.03)";
      ctx.fillRect(60, rowY, 340, 36);
      ctx.fillStyle = "#4b5563";
      ctx.font = '13px "Noto Sans SC", sans-serif';
      ctx.fillText(spec.label, 75, rowY + 23);
      ctx.fillStyle = "#1e293b";
      ctx.font = 'bold 13px "Noto Sans SC", sans-serif';
      ctx.fillText(spec.val, 190, rowY + 23);
      rowY += 50;
    });
  }

  function paintWarranty(ctx, typeId, width, height) {
    if (typeId !== "warranty") return;

    ctx.strokeStyle = THEME_COLORS.primary;
    ctx.lineWidth = 4;
    ctx.strokeRect(20, 20, width - 40, height - 40);
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(width / 2 - 180, 10, 360, 48);
    ctx.strokeStyle = THEME_COLORS.primary;
    ctx.strokeRect(width / 2 - 180, 10, 360, 48);
    ctx.fillStyle = THEME_COLORS.primaryDark;
    ctx.font = 'bold 20px "Noto Sans SC", sans-serif';
    ctx.textAlign = "center";
    ctx.fillText("官方金牌售后保障", width / 2, 42);
    ctx.textAlign = "left";

    const badges = [
      { title: "7天无理由退换", desc: "开箱试用不满意 无损极速全额退" },
      { title: "全包顺丰发货", desc: "全国主要城市 24小时闪电送达" },
      { title: "1年全保只换不修", desc: "非人为硬件故障 官方极速寄换新品" },
    ];

    let badgeY = height * 0.58;
    badges.forEach((badge) => {
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.roundRect(width / 2 - 250, badgeY, 500, 70, 10);
      ctx.fill();
      ctx.strokeStyle = "rgba(16, 185, 129, 0.25)";
      ctx.stroke();
      ctx.fillStyle = THEME_COLORS.primary;
      ctx.beginPath();
      ctx.arc(width / 2 - 210, badgeY + 35, 16, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = 'bold 16px "Noto Sans SC", sans-serif';
      ctx.fillText("✓", width / 2 - 216, badgeY + 41);
      ctx.fillStyle = THEME_COLORS.slate900;
      ctx.font = 'bold 16px "Noto Sans SC", sans-serif';
      ctx.fillText(badge.title, width / 2 - 180, badgeY + 30);
      ctx.fillStyle = THEME_COLORS.slate500;
      ctx.font = '12px "Noto Sans SC", sans-serif';
      ctx.fillText(badge.desc, width / 2 - 180, badgeY + 52);
      badgeY += 90;
    });
  }

  function paintDetailZoom(ctx, typeId, width, height) {
    if (typeId !== "detail-zoom") return;

    ctx.strokeStyle = THEME_COLORS.primary;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(width * 0.35, height * 0.5);
    ctx.lineTo(width * 0.65, height * 0.25);
    ctx.lineTo(width * 0.8, height * 0.25);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(width * 0.75, height * 0.48, 80, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = THEME_COLORS.primary;
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.fillStyle = THEME_COLORS.primary;
    ctx.fillRect(width * 0.75 - 30, height * 0.48 - 20, 60, 10);
    ctx.fillStyle = THEME_COLORS.slate900;
    ctx.font = 'bold 11px "Plus Jakarta Sans", sans-serif';
    ctx.fillText("AI MICRO CHIP", width * 0.75 - 40, height * 0.48 + 15);
    ctx.font = 'bold 16px "Noto Sans SC", sans-serif';
    ctx.fillText("精细工艺微雕", width * 0.58, height * 0.21);
  }

  function paintPlatformBadge(ctx, width) {
    ctx.fillStyle = THEME_COLORS.slate100;
    ctx.beginPath();
    ctx.roundRect(width - 170, 20, 150, 28, 6);
    ctx.fill();
    ctx.strokeStyle = "rgba(16, 185, 129, 0.2)";
    ctx.stroke();
    ctx.fillStyle = "#1e293b";
    ctx.font = 'bold 11px "Plus Jakarta Sans", sans-serif';
    ctx.fillText(`NodePass AI x ${settings.platform}`, width - 158, 38);
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
    if (selectedCards.value.length === 0) {
      toast.info("请先勾选需要下载的主图");
      return;
    }

    selectedCards.value.forEach((card, index) => {
      window.setTimeout(() => {
        downloadSingleImage(card);
      }, index * 150);
    });
  }

  function downloadSingleImage(card) {
    downloadDataUrl(card.dataUrl, `${currentTaskTitle.value}_${getModuleName(card.typeId)}.png`);
  }

  async function regenerateSingleCard(card) {
    if (uploadedImages.value.length === 0) {
      toast.info("请先上传产品图");
      return;
    }

    const mainImg = uploadedImages.value[mainImageIndex.value];
    card.dataUrl = await renderCardImage(
      card.typeId,
      getImageSrc(mainImg),
      findModuleContent(card.typeId, card),
    );
    toast.success(`${getModuleName(card.typeId)} 已重新生成`);
  }

  function previewLongImage() {
    if (selectedCards.value.length === 0) {
      toast.info("请至少勾选一张主图进行长图拼接");
      return;
    }
    showLongPreviewModal.value = true;
  }

  function downloadLongCombinedImage() {
    if (selectedCards.value.length === 0) return;

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const { width, height } = getCardSize();
    canvas.width = width;
    canvas.height = height * selectedCards.value.length;

    let loadedCount = 0;
    selectedCards.value.forEach((card, index) => {
      const img = new window.Image();
      img.onload = () => {
        ctx.drawImage(img, 0, index * height, width, height);
        loadedCount += 1;
        if (loadedCount === selectedCards.value.length) {
          downloadDataUrl(
            canvas.toDataURL("image/png"),
            `${currentTaskTitle.value}_详情拼接长图.png`,
          );
        }
      };
      img.src = card.dataUrl;
    });
  }

  function loadHistoryTask(history) {
    currentTaskTitle.value = history.title;
    settings.platform = history.platform;
    outputCards.value = JSON.parse(JSON.stringify(history.cards));
    workflowStep.value = "result";
    showHistoryDrawer.value = false;
  }

  function findModuleContent(typeId, card = null) {
    return (
      moduleContents.value.find((module) => module.id === typeId) || {
        id: typeId,
        moduleName: getModuleName(typeId),
        title: card?.strategyTitle || getModuleName(typeId),
        content: card?.strategyContent || getModuleStrategy(typeId),
        strategy: getModuleStrategy(typeId),
      }
    );
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
  }

  function removeModuleContent(index) {
    moduleContents.value = moduleContents.value.filter((_, currentIndex) => currentIndex !== index);
  }

  function backToConfig() {
    workflowStep.value = "config";
  }

  function downloadDataUrl(dataUrl, fileName) {
    const link = document.createElement("a");
    link.href = dataUrl;
    link.download = fileName;
    link.click();
  }

  return {
    uploadedImages,
    mainImageIndex,
    selectedModules,
    currentTaskTitle,
    generating,
    generatedCount,
    genLogs,
    outputCards,
    showHistoryDrawer,
    showQueueDrawer,
    showLongPreviewModal,
    zoomCard,
    aiLoading,
    workflowStep,
    strategyBrief,
    moduleContents,
    settings,
    taskQueue,
    historyTasks,
    canGenerate,
    strategyLoading,
    strategyPanelVisible,
    selectedCards,
    selectedCardsCount,
    generationProgressClass,
    selectedImageLabel,
    longPreviewHeight,
    showNotice: toast.info,
    generateSellingPointsWithAI,
    hasGenerationSource,
    getModuleName,
    getModuleStrategy,
    getProgressWidthClass,
    triggerStrategyGeneration,
    confirmStrategyAndGenerate,
    triggerBatchGeneration,
    updateModuleContent,
    reorderModuleContents,
    removeModuleContent,
    backToConfig,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleImage,
    regenerateSingleCard,
    previewLongImage,
    downloadLongCombinedImage,
    loadHistoryTask,
  };
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function makeCardId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function getProductNameFromInput(input) {
  return (
    input
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)[0] || "当前商品"
  );
}

function parseStrategyLines(content) {
  return content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function buildModuleTitle(module, productName) {
  const titleMap = {
    "first-screen": `${productName} 爆款首屏主视觉`,
    "core-selling": `${productName} 核心卖点提炼`,
    "use-scenario": `${productName} 高转化使用场景`,
    "multi-angle": `${productName} 多角度细节呈现`,
    "ambient-scene": `${productName} 场景氛围大片`,
    "detail-zoom": `${productName} 关键细节放大`,
    "brand-story": `${productName} 品牌价值表达`,
    "specs-info": `${productName} 尺寸规格说明`,
    "contrast-effect": `${productName} 效果对比表达`,
    "tech-specs": `${productName} 参数表视觉化`,
    manufacturing: `${productName} 工艺结构拆解`,
    freebies: `${productName} 配件赠品展示`,
    "series-show": `${productName} 系列 SKU 展示`,
    ingredients: `${productName} 成分信息展示`,
    warranty: `${productName} 售后保障承诺`,
    "usage-tips": `${productName} 使用建议说明`,
  };

  return titleMap[module.id] || `${productName} ${module.name}`;
}

function buildModuleContent(module, index) {
  const baseContents = [
    `模块目标：${module.desc}`,
    `排版策略：${module.strategy}`,
    `视觉重点：突出商品主体，减少无效装饰，保持电商平台可读性。`,
  ];

  const directionMap = {
    "first-screen": [
      "主标题：首屏 3 秒内传达核心价值",
      "副标题：强化新品、高端、官方背书",
      "画面层级：商品居中放大，品牌信息轻量点缀",
    ],
    "core-selling": [
      "卖点 1：核心性能升级",
      "卖点 2：材质与工艺优势",
      "卖点 3：服务保障降低决策成本",
    ],
    "use-scenario": [
      "场景：真实使用环境",
      "情绪：干净、可信、有生活感",
      "信息：保留一个强卖点即可",
    ],
    "multi-angle": [
      "视角：正面、侧面、细节局部",
      "对齐：统一比例与基线",
      "标注：只保留关键结构名称",
    ],
    "detail-zoom": [
      "细节：局部材质、接口、工艺纹理",
      "标注：拉线说明关键优势",
      "氛围：保持精密感与可信度",
    ],
    warranty: ["信任点：退换、发货、质保", "表达：徽章式信息块", "语气：官方、明确、降低售后疑虑"],
  };

  const lines = directionMap[module.id] || baseContents;
  return [`模块序号：${index + 1}`, ...lines].join("\n");
}

function getProgressWidthClass(progress) {
  if (progress >= 100) return "w-full";
  if (progress >= 90) return "w-11/12";
  if (progress >= 75) return "w-3/4";
  if (progress >= 66) return "w-2/3";
  if (progress >= 50) return "w-1/2";
  if (progress >= 33) return "w-1/3";
  if (progress >= 25) return "w-1/4";
  if (progress > 0) return "w-1/12";
  return "w-0";
}

function getImageSrc(image) {
  if (!image) return "";
  if (typeof image === "string") return image;
  return image.previewUrl || image.url || "";
}
