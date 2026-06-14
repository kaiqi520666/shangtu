import { computed, ref } from "vue";
import JSZip from "jszip";
import { getImageDownloadUrl } from "@/api/image.js";
import { useAuthStore } from "@/stores/auth.js";

/**
 * 通用卡片操作：选择、下载（单张 / 批量 zip）、缩放。
 * 与场景无关，由各场景 composable 组合使用。
 *
 * @param {Object} deps
 * @param {import('vue').Ref<Array>} deps.outputCards - 卡片数组 ref
 * @param {import('vue').Ref<string>} deps.currentTaskTitle - 当前任务标题 ref（用于文件名）
 * @param {Function} deps.getCardName - (card) => string，用于文件命名
 * @param {Object} deps.toast - useToast 实例
 */
export function useCardActions({ outputCards, currentTaskTitle, getCardName, toast }) {
  const zoomCard = ref(null);
  const authStore = useAuthStore();

  const selectedCards = computed(() => outputCards.value.filter((card) => card.selected));
  const selectedCardsCount = computed(() => selectedCards.value.length);

  function toggleCardSelection(id) {
    const card = outputCards.value.find((item) => item.id === id);
    if (card) card.selected = !card.selected;
  }

  function toggleSelectAllCards(value) {
    outputCards.value.forEach((card) => {
      card.selected = value;
    });
  }

  // --- 下载 ---

  function batchDownload() {
    const downloadable = selectedCards.value.filter(
      (card) => card.status === "done" && card.dataUrl,
    );
    if (downloadable.length === 0) {
      toast.info("请先勾选已生成完成的图片");
      return;
    }

    if (downloadable.length === 1) {
      downloadSingleImage(downloadable[0]);
      return;
    }

    downloadAsZip(downloadable);
  }

  async function downloadAsZip(cards) {
    toast.info(`正在打包 ${cards.length} 张图片...`);
    const zip = new JSZip();
    const token = authStore.token;

    const results = await Promise.allSettled(
      cards.map(async (card, index) => {
        const url = getImageDownloadUrl(card.taskId);
        const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        const ext = blob.type === "image/jpeg" ? "jpg" : "png";
        const name = `${getCardName(card) || `image_${index + 1}`}_${index + 1}.${ext}`;
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
      link.download = `${currentTaskTitle.value || "生成图片"}.zip`;
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
      toast.info("该图片还未生成完成");
      return;
    }
    try {
      const url = getImageDownloadUrl(card.taskId);
      const token = authStore.token;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const ext = blob.type === "image/jpeg" ? "jpg" : "png";
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `${currentTaskTitle.value}_${getCardName(card)}.${ext}`;
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

  return {
    zoomCard,
    selectedCards,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleImage,
    downloadAsZip,
  };
}
