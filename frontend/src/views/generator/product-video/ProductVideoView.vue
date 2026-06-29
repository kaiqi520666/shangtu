<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import GenerationHistoryDrawer from "@/components/generation/workspace/GenerationHistoryDrawer.vue";
import GenerationPreviewModal from "@/components/generation/workspace/GenerationPreviewModal.vue";
import GenerationWorkspace from "@/components/generation/workspace/GenerationWorkspace.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import ProductVideoStrategyReviewPanel from "@/components/product-video/ProductVideoStrategyReviewPanel.vue";
import VideoSettingsPanel from "@/components/product-video/VideoSettingsPanel.vue";
import { useGeneratorRouteJob } from "@/composables/generator/restore/useGeneratorRouteJob.js";
import { useProductVideoGenerator } from "@/composables/generator/useProductVideoGenerator.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";
import { videoDemoTypes } from "@/constants/product-video.js";

const route = useRoute();
const router = useRouter();
const confirm = useConfirm();
const toast = useToast();
const video = useProductVideoGenerator({
  toast,
  onJobCreated(jobId) {
    router.replace(`/generator/product-video/${jobId}`);
  },
});
const zoomCard = ref(null);

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator: video,
  route,
  router,
  basePath: "/generator/product-video",
  toast,
  confirm,
});

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

function closeHistoryDrawer() {
  video.showHistoryDrawer.value = false;
}
</script>

<template>
  <GeneratorLayout>
    <ProductVideoStrategyReviewPanel
      v-if="video.strategyPanelVisible.value"
      placement="side"
      :loading="video.strategyLoading.value"
      :brief="video.strategyBrief.value"
      :items="video.videoStrategyItems.value"
      :meta-text="video.strategyMetaText.value"
      :dirty="video.strategyDirty.value"
      :estimated-credits="video.estimatedCredits.value"
      @back="video.backToConfig"
      @confirm="video.confirmStrategyAndGenerate"
      @update-script="video.updateVideoScript"
    />

    <VideoSettingsPanel
      v-else
      :settings="video.settings"
      :uploaded-images="video.uploadedImages.value"
      :main-image-index="video.mainImageIndex.value"
      :credit-costs="video.creditCosts.value"
      :can-generate-strategy="video.canGenerateStrategy.value"
      :strategy-loading="video.strategyLoading.value"
      @update:settings="video.updateSettings"
      @update:uploaded-images="video.uploadedImages.value = $event"
      @update:main-image-index="video.mainImageIndex.value = $event"
      @notify="video.showNotice"
      @generate-strategy="video.triggerStrategyGeneration"
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
      :downloading="video.downloading.value"
      selected-image-label="商品视频"
      :get-module-name="video.getVideoModuleName"
      empty-title="商品视频示例"
      empty-subtitle="这里仅用于预览不同电商视频风格，左侧选择的视频方向才会影响生成设置。"
      :empty-slides="videoDemoTypes"
      media-type="video"
      media-unit="个"
      loading-title="AI 商品视频生成中"
      loading-description="正在创建商品视频任务，稍后会在右侧显示生成进度"
      progress-text="正在生成商品视频"
      poll-hint="每 3 秒轮询任务状态"
      @update:current-task-title="video.updateCurrentJobTitle"
      @select-all-cards="video.toggleSelectAllCards"
      @batch-download="video.batchDownload"
      @toggle-card="video.toggleCardSelection"
      @download-card="video.downloadSingleVideo"
      @zoom-card="openPreview"
      @delete-card="video.removeCard"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="video.showHistoryDrawer.value"
      :jobs="video.historyTasks.value"
      :loading="video.historyLoading.value"
      :current-job-id="video.currentJobId.value"
      empty-hint="点击「新建任务」开始生成商品视频"
      unit="个"
      @close="closeHistoryDrawer"
      @pick="pickHistory"
      @delete="handleDeleteJob"
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
