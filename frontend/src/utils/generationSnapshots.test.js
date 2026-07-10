import { describe, expect, it } from "vitest";
import { applyImageCapabilities } from "@/constants/generator.js";
import {
  cloneUploadedImages,
  restoreImageGenerationSettings,
  syncImageQuality,
} from "./generationSnapshots.js";

describe("generation snapshot helpers", () => {
  it("clones only persisted upload fields", () => {
    expect(cloneUploadedImages([{ id: "1", url: "remote", previewUrl: "local", uploading: true }])).toEqual([
      {
        id: "1",
        url: "remote",
        objectKey: undefined,
        contentType: undefined,
        size: undefined,
        previewUrl: "remote",
      },
    ]);
  });

  it("restores supported image settings and normalizes quality", () => {
    applyImageCapabilities({ "3:4": { "1K": [768, 1024], "2K": [1536, 2048] } });
    const settings = { platform: "", language: "", ratio: "1:1", quality: "4K" };
    restoreImageGenerationSettings(settings, {
      platform: "Amazon",
      language: "English",
      ratio: "3:4",
      quality: "2K",
    });
    expect(settings).toEqual({ platform: "Amazon", language: "English", ratio: "3:4", quality: "2K" });
  });

  it("keeps quality valid when ratio changes", () => {
    const settings = { ratio: "9:16", quality: "4K" };
    syncImageQuality(settings);
    expect(settings.quality).toBeTruthy();
  });
});
