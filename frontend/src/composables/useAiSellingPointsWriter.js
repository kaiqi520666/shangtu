import { ref } from "vue";
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
  const aiLoading = ref(false);

  async function generateSellingPointsWithAI() {
    const validationMessage = validate?.() || "";
    if (validationMessage) {
      toast?.info?.(validationMessage);
      return "";
    }

    const images = buildImages?.() || [];
    if (images.length === 0) {
      toast?.info?.(emptyMessage);
      return "";
    }

    const uploadedImages = getUploadedImages?.() || [];
    if (hasUploadingImages(uploadedImages)) {
      toast?.info?.(uploadingMessage);
      return "";
    }

    aiLoading.value = true;
    try {
      const result = await analyzeImage({
        images,
        ...(getAnalyzePayload?.() || {}),
      });
      if (result.code !== 0) {
        toast?.error?.(result.message || "AI 分析失败，请稍后重试");
        return "";
      }

      const content = result.data?.content?.trim();
      if (!content) {
        toast?.error?.("AI 未返回有效内容");
        return "";
      }
      return content;
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast?.error?.("登录已过期，请重新登录");
      } else {
        toast?.error?.(error.response?.data?.message || "AI 分析失败，请稍后重试");
      }
      return "";
    } finally {
      aiLoading.value = false;
    }
  }

  return {
    aiLoading,
    generateSellingPointsWithAI,
  };
}
