import { computed, ref } from "vue";
import JSZip from "jszip";
import { getImageDownloadUrl } from "@/api/image.js";
import { useAuthStore } from "@/stores/auth.js";

function defaultBlobExtension(blob) {
  if (blob.type === "image/jpeg") return "jpg";
  if (blob.type === "image/webp") return "webp";
  if (blob.type === "video/webm") return "webm";
  if (blob.type === "video/quicktime") return "mov";
  if (blob.type === "video/mp4") return "mp4";
  return "png";
}

function triggerBlobDownload(url, filename) {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function openFallbackUrl(url) {
  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener";
  link.click();
}

/**
 * 通用卡片操作：选择、下载（单个 / 批量 zip）、缩放。
 * 与场景无关，由各场景 composable 组合使用。
 *
 * @param {Object} deps
 * @param {import('vue').Ref<Array>} deps.outputCards - 卡片数组 ref
 * @param {import('vue').Ref<string>} deps.currentTaskTitle - 当前任务标题 ref（用于文件名）
 * @param {Function} deps.getCardName - (card) => string，用于文件命名
 * @param {Function} [deps.getDownloadUrl] - (card) => string，用于按媒体类型取下载地址
 * @param {Function} [deps.getBlobExtension] - (blob, card) => string，用于文件扩展名
 * @param {Object} deps.toast - useToast 实例
 */
export function useCardActions({
  outputCards,
  currentTaskTitle,
  getCardName,
  getDownloadUrl = (card) => getImageDownloadUrl(card.taskId),
  getBlobExtension = defaultBlobExtension,
  toast,
  mediaLabel = "图片",
  mediaUnit = "张",
  archiveName = "生成图片",
}) {
  const zoomCard = ref(null);
  const downloading = ref(false);
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
    if (downloading.value) {
      toast.info("下载处理中，请稍候");
      return;
    }

    const downloadable = selectedCards.value.filter(
      (card) => card.status === "done" && card.dataUrl,
    );
    if (downloadable.length === 0) {
      toast.info(`请先勾选已生成完成的${mediaLabel}`);
      return;
    }

    if (downloadable.length === 1) {
      downloadSingleMedia(downloadable[0]);
      return;
    }

    downloadAsZip(downloadable);
  }

  async function downloadAsZip(cards) {
    if (downloading.value) {
      toast.info("下载处理中，请稍候");
      return;
    }

    downloading.value = true;
    cards.forEach((card) => {
      card.downloading = true;
    });
    try {
      toast.info(`正在打包 ${cards.length} ${mediaUnit}${mediaLabel}...`);
      const zip = new JSZip();
      const token = authStore.token;

      const results = await Promise.allSettled(
        cards.map(async (card, index) => {
          const url = getDownloadUrl(card);
          const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const blob = await res.blob();
          const ext = getBlobExtension(blob, card);
          const name = `${getCardName(card) || `asset_${index + 1}`}_${index + 1}.${ext}`;
          zip.file(name, blob);
        }),
      );

      const succeeded = results.filter((r) => r.status === "fulfilled").length;
      if (succeeded === 0) {
        toast.error(`${mediaLabel}下载失败，请稍后重试`);
        return;
      }

      const content = await zip.generateAsync({ type: "blob" });
      const url = URL.createObjectURL(content);
      triggerBlobDownload(url, `${currentTaskTitle.value || archiveName}.zip`);
      if (succeeded < cards.length) {
        toast.info(`已打包 ${succeeded}/${cards.length} ${mediaUnit}，部分${mediaLabel}下载失败`);
      } else {
        toast.success("打包下载完成");
      }
    } catch {
      toast.error("打包失败，请稍后重试");
    } finally {
      cards.forEach((card) => {
        card.downloading = false;
      });
      downloading.value = false;
    }
  }

  async function downloadSingleMedia(card) {
    if (!card.dataUrl) {
      toast.info(`该${mediaLabel}还未生成完成`);
      return;
    }

    if (downloading.value || card.downloading) {
      toast.info("下载处理中，请稍候");
      return;
    }

    downloading.value = true;
    card.downloading = true;
    try {
      toast.info(`正在准备${mediaLabel}下载...`);
      const url = getDownloadUrl(card);
      const token = authStore.token;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const ext = getBlobExtension(blob, card);
      const blobUrl = URL.createObjectURL(blob);
      triggerBlobDownload(blobUrl, `${currentTaskTitle.value}_${getCardName(card)}.${ext}`);
    } catch {
      // fallback 到直接打开
      openFallbackUrl(card.dataUrl);
    } finally {
      card.downloading = false;
      downloading.value = false;
    }
  }

  return {
    zoomCard,
    downloading,
    selectedCards,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleMedia,
    downloadSingleImage: downloadSingleMedia,
    downloadAsZip,
  };
}
