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
  voiceId,
  voiceName,
  voiceLanguage,
  voicePreviewAudioUrl,
  script,
  motionPrompt,
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
      voiceId,
      voiceName,
      voiceLanguage,
      voicePreviewAudioUrl,
      script,
      motionPrompt,
      qualityTier,
      resolution,
      aspectRatio,
      voiceSettings: voiceSettings && typeof voiceSettings === "object" ? cloneSnapshotValue(voiceSettings) : {},
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
