// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useFreeImageGenerator } from "@/composables/generator/useFreeImageGenerator.js";
import { useFreeVideoGenerator } from "@/composables/generator/useFreeVideoGenerator.js";
import { useAiSellingPointsWriter } from "@/composables/useAiSellingPointsWriter.js";

const mocks = vi.hoisted(() => ({
  analyzeImage: vi.fn(),
  optimizeImage: vi.fn(),
  optimizeVideo: vi.fn(),
  toast: {
    error: vi.fn(),
    info: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("@/api/image.js", () => ({
  analyzeImage: mocks.analyzeImage,
  getImageTask: vi.fn(),
  optimizeFreeImagePrompt: mocks.optimizeImage,
}));

vi.mock("@/api/video.js", () => ({
  deleteVideoTask: vi.fn(),
  generateVideo: vi.fn(),
  getVideoCreditCosts: vi.fn(),
  getVideoDownloadUrl: vi.fn(),
  getVideoTask: vi.fn(),
  optimizeFreeVideoPrompt: mocks.optimizeVideo,
}));

vi.mock("@/composables/useToast.js", () => ({
  useToast: () => mocks.toast,
}));

describe("AI draft generators", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("supplies image analysis as a draft", async () => {
    mocks.analyzeImage.mockImplementation(async (_payload, { onChunk }) => {
      onChunk("商品卖点草稿");
    });
    const writer = useAiSellingPointsWriter({
      toast: mocks.toast,
      buildImages: () => [{ url: "https://example.com/product.jpg" }],
      getUploadedImages: () => [],
      getAnalyzePayload: () => ({ scenario: "product_image" }),
    });
    const onChunk = vi.fn();
    const controller = new AbortController();

    const ok = await writer.generateSellingPointsWithAI({ signal: controller.signal, onChunk });

    expect(mocks.analyzeImage).toHaveBeenCalledWith(
      expect.objectContaining({ scenario: "product_image" }),
      { signal: controller.signal, onChunk },
    );
    expect(onChunk).toHaveBeenCalledWith("商品卖点草稿");
    expect(ok).toBe(true);
  });

  it("supplies optimized image text without overwriting the source", async () => {
    mocks.optimizeImage.mockImplementation(async (_prompt, { onChunk }) => {
      onChunk("图片优化草稿");
    });
    const generator = useFreeImageGenerator();
    generator.settings.prompt = "图片原文";
    const onChunk = vi.fn();
    const controller = new AbortController();

    const ok = await generator.optimizePrompt({ signal: controller.signal, onChunk });

    expect(mocks.optimizeImage).toHaveBeenCalledWith("图片原文", {
      signal: controller.signal,
      onChunk,
    });
    expect(onChunk).toHaveBeenCalledWith("图片优化草稿");
    expect(generator.settings.prompt).toBe("图片原文");
    expect(ok).toBe(true);
  });

  it("supplies optimized video text and reports API failures", async () => {
    const generator = useFreeVideoGenerator();
    generator.settings.prompt = "视频原文";
    const controller = new AbortController();
    const onChunk = vi.fn();
    mocks.optimizeVideo.mockImplementationOnce(async (_prompt, { onChunk: writeChunk }) => {
      writeChunk("视频优化草稿");
    });

    expect(await generator.optimizePrompt({ signal: controller.signal, onChunk })).toBe(true);
    expect(onChunk).toHaveBeenCalledWith("视频优化草稿");
    expect(generator.settings.prompt).toBe("视频原文");

    const error = new Error("优化服务忙");
    error.response = { data: { message: "优化服务忙" } };
    mocks.optimizeVideo.mockRejectedValueOnce(error);
    expect(await generator.optimizePrompt({ signal: controller.signal, onChunk })).toBe(false);
    expect(mocks.toast.error).toHaveBeenCalledWith("优化服务忙");
  });

  it("does not show an error after cancellation", async () => {
    const generator = useFreeImageGenerator();
    generator.settings.prompt = "图片原文";
    const controller = new AbortController();
    controller.abort();
    mocks.optimizeImage.mockRejectedValue(new Error("canceled"));

    expect(await generator.optimizePrompt({ signal: controller.signal, onChunk: vi.fn() })).toBe(false);
    expect(mocks.toast.error).not.toHaveBeenCalled();
  });
});
