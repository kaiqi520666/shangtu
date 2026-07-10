function cloneSnapshotValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => cloneSnapshotValue(item));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, cloneSnapshotValue(item)]),
    );
  }
  return value;
}

export function createGenerationSettingsSnapshot({
  scenario,
  mediaType = "image",
  platform = "",
  language = "",
  ratio = "",
  quality = "",
  scene = {},
} = {}) {
  return {
    scenario,
    media_type: mediaType,
    platform,
    language,
    ratio,
    quality,
    scene: scene && typeof scene === "object" ? cloneSnapshotValue(scene) : {},
  };
}

export function createVideoSettingsSnapshot({
  videoType,
  title,
  inputMode,
  market,
  marketLabel,
  language,
  languageLabel,
  sizePreset,
  aspectRatio,
  duration,
  resolution,
  productInput,
} = {}) {
  return createGenerationSettingsSnapshot({
    scenario: "product_video",
    mediaType: "video",
    platform: market,
    language,
    ratio: aspectRatio,
    quality: resolution,
    scene: {
      videoType,
      title,
      inputMode,
      market,
      marketLabel,
      language,
      languageLabel,
      sizePreset,
      aspectRatio,
      duration,
      resolution,
      productInput,
    },
  });
}

export function createDigitalHumanSettingsSnapshot({
  avatarId,
  avatarName,
  avatarPreviewImageUrl,
  avatarPreviewVideoUrl,
  avatarSource,
  avatarAssetId,
  avatarType,
  audioMode,
  voiceId,
  voiceName,
  voiceLanguage,
  voicePreviewAudioUrl,
  audioAssetId,
  audioName,
  audioUrl,
  audioDurationSeconds,
  backgroundUrl,
  script,
  qualityTier,
  resolution,
  aspectRatio,
  voiceSettings,
} = {}) {
  return createGenerationSettingsSnapshot({
    scenario: "digital_human",
    mediaType: "video",
    language: voiceLanguage || "",
    ratio: aspectRatio || "",
    quality: resolution || "",
    scene: {
      avatarId,
      avatarName,
      avatarPreviewImageUrl,
      avatarPreviewVideoUrl,
      avatarSource,
      avatarAssetId,
      avatarType,
      audioMode,
      voiceId,
      voiceName,
      voiceLanguage,
      voicePreviewAudioUrl,
      audioAssetId,
      audioName,
      audioUrl,
      audioDurationSeconds,
      backgroundUrl,
      script,
      qualityTier,
      resolution,
      aspectRatio,
      voiceSettings: voiceSettings && typeof voiceSettings === "object" ? cloneSnapshotValue(voiceSettings) : {},
    },
  });
}

export function createVideoTranslationSettingsSnapshot({
  videoUrl,
  targetLanguageId,
  targetLanguageName,
  targetLanguageDisplayNameZh,
  qualityTier,
  durationSeconds,
  perSecondCost,
  creditCost,
  source,
  assetTaskId,
} = {}) {
  return createGenerationSettingsSnapshot({
    scenario: "video_translation",
    mediaType: "video",
    language: targetLanguageName || "",
    ratio: "original",
    quality: qualityTier || "",
    scene: {
      videoUrl,
      targetLanguageId,
      targetLanguageName,
      targetLanguageDisplayNameZh,
      qualityTier,
      durationSeconds,
      perSecondCost,
      creditCost,
      source,
      assetTaskId,
    },
  });
}

export function getSnapshotScene(snapshot) {
  return snapshot && typeof snapshot.scene === "object" && snapshot.scene !== null
    ? snapshot.scene
    : {};
}

export function getSnapshotQuality(snapshot, fallback = "1K") {
  return snapshot?.quality || fallback;
}

export function cloneGenerationSettingsSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object") return null;
  return cloneSnapshotValue(snapshot);
}

export function cloneUploadedImages(images) {
  return images.map((image) => ({
    id: image.id,
    url: image.url,
    objectKey: image.objectKey,
    contentType: image.contentType,
    size: image.size,
    previewUrl: image.url || image.previewUrl,
  }));
}

export function restoreImageGenerationSettings(settings, snapshot) {
  if (!snapshot || typeof snapshot !== "object") return;
  if (typeof snapshot.platform === "string") settings.platform = snapshot.platform;
  if (typeof snapshot.language === "string") settings.language = snapshot.language;
  if (typeof snapshot.ratio === "string" && resolutionMap[snapshot.ratio]) {
    settings.ratio = snapshot.ratio;
  }
  const quality = typeof snapshot.quality === "string" ? snapshot.quality : settings.quality;
  settings.quality = resolveQuality(settings.ratio, quality) || "1K";
}

export function syncImageQuality(settings) {
  const quality = resolveQuality(settings.ratio, settings.quality) || settings.quality;
  if (quality !== settings.quality) settings.quality = quality;
}
import { resolutionMap, resolveQuality } from "@/constants/generator.js";
