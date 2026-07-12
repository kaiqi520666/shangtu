import { buildVideoAnalyzeImages } from "@/utils/analyzeImages.js";
import { createVideoSettingsSnapshot } from "@/utils/generationSnapshots.js";
import {
  getVideoDemoType,
  videoLanguageOptions,
  videoMarketOptions,
  videoSizeOptions,
} from "@/constants/product-video.js";

export function getVideoOptionLabel(options, value) {
  return options.find((item) => item.value === value)?.label || value;
}

export function getSelectedVideoSize(sizePreset) {
  return (
    videoSizeOptions.find((item) => item.value === sizePreset) ||
    videoSizeOptions[0]
  );
}

export function getRequiredVideoImageMessage(inputMode, count) {
  if (inputMode === "reference_to_video" && (count < 1 || count > 9)) {
    return "请上传 1-9 张参考图";
  }
  return "";
}

export function buildProductVideoStrategySnapshot(settings, uploadedImages) {
  const selectedType = getVideoDemoType(settings.videoType);
  const selectedSize = getSelectedVideoSize(settings.sizePreset);
  return {
    scenario: "product_video",
    type_id: selectedType.typeId,
    input_mode: selectedType.inputMode,
    market: settings.market,
    language: settings.language,
    duration: settings.duration,
    aspect_ratio: selectedSize.aspectRatio,
    product_input: settings.productInput,
    images: buildVideoAnalyzeImages(selectedType.inputMode, uploadedImages),
  };
}

export function buildProductVideoSettingsSnapshot(settings, strategyBrief = "") {
  const selectedType = getVideoDemoType(settings.videoType);
  const selectedSize = getSelectedVideoSize(settings.sizePreset);
  const snapshot = createVideoSettingsSnapshot({
    videoType: settings.videoType,
    title: selectedType.title,
    inputMode: selectedType.inputMode,
    market: settings.market,
    marketLabel: getVideoOptionLabel(videoMarketOptions, settings.market),
    language: settings.language,
    languageLabel: getVideoOptionLabel(videoLanguageOptions, settings.language),
    sizePreset: settings.sizePreset,
    aspectRatio: selectedSize.aspectRatio,
    duration: settings.duration,
    resolution: settings.resolution,
    productInput: settings.productInput,
  });
  return {
    ...snapshot,
    scene: {
      ...snapshot.scene,
      strategyBrief,
    },
  };
}

export function normalizeVideoStrategyItems(items, videoType) {
  const source = Array.isArray(items) ? items : [];
  return source.slice(0, 1).map((item) => {
    const type = getVideoDemoType(item.id || videoType);
    return {
      id: item.id || type.typeId,
      name: item.name || type.title,
      content: item.content || "",
    };
  });
}

export function getConfirmedVideoScript(items) {
  return (items[0]?.content || "").trim();
}
