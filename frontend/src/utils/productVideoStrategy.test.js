import { describe, expect, it } from "vitest";
import { videoDemoTypes } from "@/constants/product-video.js";
import {
  buildProductVideoSettingsSnapshot,
  buildProductVideoStrategySnapshot,
  getConfirmedVideoScript,
  getRequiredVideoImageMessage,
  normalizeVideoStrategyItems,
} from "./productVideoStrategy.js";

const settings = {
  videoType: videoDemoTypes[0].typeId,
  market: "global",
  language: "english",
  sizePreset: "tiktok_9_16",
  duration: 8,
  resolution: "720p",
  productInput: "轻便耐用",
};

describe("product video strategy helpers", () => {
  it("validates reference image counts", () => {
    expect(getRequiredVideoImageMessage("reference_to_video", 0)).toBe(
      "请上传 1-9 张参考图",
    );
    expect(getRequiredVideoImageMessage("reference_to_video", 10)).toBe(
      "请上传 1-9 张参考图",
    );
    expect(getRequiredVideoImageMessage("reference_to_video", 1)).toBe("");
    expect(getRequiredVideoImageMessage("image_to_video", 0)).toBe("");
  });

  it("builds strategy and persisted snapshots from current settings", () => {
    const strategy = buildProductVideoStrategySnapshot(settings, [
      { url: "image-1" },
      { uploading: true },
    ]);
    const persisted = buildProductVideoSettingsSnapshot(settings, "策略摘要");

    expect(strategy).toMatchObject({
      scenario: "product_video",
      market: "global",
      language: "english",
      duration: 8,
      aspect_ratio: "9:16",
      product_input: "轻便耐用",
      images: [{ url: "image-1", label: "参考图1" }],
    });
    expect(persisted).toMatchObject({
      scenario: "product_video",
      media_type: "video",
      platform: "global",
      language: "english",
      ratio: "9:16",
      quality: "720p",
      scene: {
        strategyBrief: "策略摘要",
        productInput: "轻便耐用",
      },
    });
  });

  it("keeps one normalized prompt and reads its trimmed content", () => {
    const items = normalizeVideoStrategyItems(
      [
        { content: "  已确认提示词  " },
        { id: "ignored", content: "不会保留" },
      ],
      settings.videoType,
    );

    expect(items).toHaveLength(1);
    expect(items[0].id).toBe(settings.videoType);
    expect(getConfirmedVideoScript(items)).toBe("已确认提示词");
    expect(getConfirmedVideoScript([])).toBe("");
  });
});
