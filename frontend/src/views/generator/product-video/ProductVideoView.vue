<script setup>
import { onMounted, ref } from "vue";
import GenerationPreviewModal from "@/components/generation/GenerationPreviewModal.vue";
import GenerationWorkspace from "@/components/generation/GenerationWorkspace.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import VideoSettingsPanel from "@/components/product-video/VideoSettingsPanel.vue";
import { useProductVideoGenerator } from "@/composables/useProductVideoGenerator.js";
import { useToast } from "@/composables/useToast.js";
import { videoDemoTypes } from "@/constants/productVideo.js";

const toast = useToast();
const video = useProductVideoGenerator({ toast });
const zoomCard = ref(null);

onMounted(() => {
  video.loadCreditCosts();
});

function openPreview(card) {
  if (card.status !== "done" || !card.dataUrl) return;
  zoomCard.value = card;
}

function closePreview() {
  zoomCard.value = null;
}
</script>

<template>
  <GeneratorLayout>
    <VideoSettingsPanel
      :settings="video.settings"
      :uploaded-images="video.uploadedImages.value"
      :main-image-index="video.mainImageIndex.value"
      :credit-costs="video.creditCosts.value"
      @update:settings="video.updateSettings"
      @update:uploaded-images="video.uploadedImages.value = $event"
      @update:main-image-index="video.mainImageIndex.value = $event"
      @notify="video.showNotice"
      @generate="video.generateProductVideo"
    />

    <GenerationWorkspace
      :settings="video.settings"
      :current-task-title="video.currentTaskTitle.value"
      :output-cards="video.outputCards.value"
      :generating="video.generating.value"
      :creating-batch="video.creatingBatch.value"
      :generated-count="video.generatedCount.value"
      :running-count="video.runningCount.value"
      :failed-count="video.failedCount.value"
      :total-count="video.jobTotal.value"
      :job-total="video.jobTotal.value"
      :gen-logs="video.genLogs.value"
      :selected-cards-count="video.selectedCardsCount.value"
      selected-image-label="商品视频"
      :get-module-name="video.getVideoModuleName"
      title-badge="商品视频任务"
      empty-title="商品视频示例"
      empty-subtitle="这里仅用于预览不同电商视频风格，左侧选择的视频方向才会影响生成设置。"
      :empty-slides="videoDemoTypes"
      empty-media-type="video"
      media-type="video"
      media-unit="个"
      loading-title="AI 商品视频生成中"
      loading-description="正在创建商品视频任务，稍后会在右侧显示生成进度"
      progress-text="正在生成商品视频"
      poll-hint="每 3 秒轮询任务状态"
      @update:current-task-title="video.currentTaskTitle.value = $event"
      @select-all-cards="video.toggleSelectAllCards"
      @batch-download="video.batchDownload"
      @toggle-card="video.toggleCardSelection"
      @download-card="video.downloadSingleVideo"
      @zoom-card="openPreview"
      @delete-card="video.removeCard"
      @create-new-task="video.showNotice('商品视频新建任务会在历史记录接入时开放')"
      @open-history="video.showNotice('商品视频生成记录会在下一批接入')"
    />

    <GenerationPreviewModal
      :card="zoomCard"
      title="商品视频预览"
      alt="商品视频预览"
      media-type="video"
      @close="closePreview"
    />
  </GeneratorLayout>
</template>
