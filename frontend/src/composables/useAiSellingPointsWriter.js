import { analyzeImage } from "@/api/image.js";
import { hasUploadingImages } from "@/utils/analyzeImages.js";

export function useAiSellingPointsWriter({
  toast,
  buildImages,
  getUploadedImages,
  getAnalyzePayload,
  validate,
  emptyMessage = "请先上传商品图，等待图片上传完成后再让 AI 帮写",
  uploadingMessage = "商品图还在上传中，请稍候",
} = {}) {
  async function generateSellingPointsWithAI({ signal, onChunk }) {
    const validationMessage = validate?.() || "";
    if (validationMessage) {
      toast?.info?.(validationMessage);
      return false;
    }

    const images = buildImages?.() || [];
    if (images.length === 0) {
      toast?.info?.(emptyMessage);
      return false;
    }

    const uploadedImages = getUploadedImages?.() || [];
    if (hasUploadingImages(uploadedImages)) {
      toast?.info?.(uploadingMessage);
      return false;
    }

    try {
      await analyzeImage({
        images,
        ...getAnalyzePayload?.(),
      }, { signal, onChunk });
      return true;
    } catch (error) {
      if (signal.aborted) return false;
      const status = error.response?.status;
      if (status === 401) {
        toast?.error?.("登录已过期，请重新登录");
      } else {
        toast?.error?.(error.response?.data?.message || "AI 分析失败，请稍后重试");
      }
      return false;
    }
  }

  return {
    generateSellingPointsWithAI,
  };
}
