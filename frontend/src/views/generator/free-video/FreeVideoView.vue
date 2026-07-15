<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import GenerationHistoryDrawer from "@/components/generation/workspace/GenerationHistoryDrawer.vue";
import GenerationPreviewModal from "@/components/generation/workspace/GenerationPreviewModal.vue";
import GenerationWorkspace from "@/components/generation/workspace/GenerationWorkspace.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import FreeVideoSettingsPanel from "@/components/free-video/FreeVideoSettingsPanel.vue";
import { useGeneratorRouteJob } from "@/composables/generator/restore/useGeneratorRouteJob.js";
import { useFreeVideoGenerator } from "@/composables/generator/useFreeVideoGenerator.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

const route = useRoute();
const router = useRouter();
const confirm = useConfirm();
const toast = useToast();
const generator = useFreeVideoGenerator({
  confirm,
  onJobCreated(jobId) {
    router.replace(`/generator/free-video/${jobId}`);
  },
});
const zoomCard = ref(null);

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator,
  route,
  router,
  basePath: "/generator/free-video",
  toast,
  confirm,
});

onMounted(() => {
  generator.loadCreditCosts();
});

function openPreview(card) {
  if (card.status !== "done" || !card.dataUrl) return;
  zoomCard.value = card;
}

function closePreview() {
  zoomCard.value = null;
}

function closeHistoryDrawer() {
  generator.showHistoryDrawer.value = false;
}
</script>

<template>
  <GeneratorLayout>
    <FreeVideoSettingsPanel
      :settings="generator.settings"
      :uploaded-images="generator.uploadedImages.value"
      :uploaded-videos="generator.uploadedVideos.value"
      :uploaded-audios="generator.uploadedAudios.value"
      :main-image-index="generator.mainImageIndex.value"
      :credit-costs="generator.creditCosts.value"
      :optimizing="generator.optimizing.value"
      :can-optimize="generator.canOptimize.value"
      :can-generate="generator.canGenerate.value"
      :creating-batch="generator.creatingBatch.value"
      :has-running-tasks="generator.hasRunningTasks.value"
      :selected-video-label="generator.selectedVideoLabel.value"
      @update:settings="generator.updateSettings"
      @update:uploaded-images="generator.uploadedImages.value = $event"
      @update:uploaded-videos="generator.uploadedVideos.value = $event"
      @update:uploaded-audios="generator.uploadedAudios.value = $event"
      @update:main-image-index="generator.mainImageIndex.value = $event"
      @notify="generator.showNotice"
      @optimize="generator.optimizePrompt"
      @generate="generator.generateFreeVideo"
    />

    <GenerationWorkspace
      :settings="generator.settings"
      :current-task-title="generator.currentTaskTitle.value"
      :output-cards="generator.outputCards.value"
      :generating="generator.generating.value"
      :creating-batch="generator.creatingBatch.value"
      :generated-count="generator.generatedCount.value"
      :running-count="generator.runningCount.value"
      :failed-count="generator.failedCount.value"
      :total-count="generator.jobTotal.value"
      :job-total="generator.jobTotal.value"
      :gen-logs="generator.genLogs.value"
      :selected-cards-count="generator.selectedCardsCount.value"
      :downloading="generator.downloading.value"
      selected-image-label="自由生视频"
      :get-module-name="generator.getModuleName"
      title-badge="本次自由生视频"
      empty-title="自由生视频"
      empty-subtitle="输入提示词，可选参考图、参考视频或参考音频，直接生成动态视频。"
      empty-image="https://image.nodepass.net/generated/2/2026/07/7bc8339f121044b1a782a7b0e8b122e4.png"
      empty-image-alt="红色风衣人物在城市中运动的电影视频画面"
      media-type="video"
      media-unit="个"
      loading-title="AI 自由生视频生成中"
      loading-description="正在创建视频任务，稍后会在右侧显示生成进度"
      progress-text="正在生成自由生视频"
      @update:current-task-title="generator.updateCurrentJobTitle"
      @select-all-cards="generator.toggleSelectAllCards"
      @batch-download="generator.batchDownload"
      @toggle-card="generator.toggleCardSelection"
      @download-card="generator.downloadSingleVideo"
      @zoom-card="openPreview"
      @delete-card="generator.removeCard"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="generator.showHistoryDrawer.value"
      :jobs="generator.historyTasks.value"
      :loading="generator.historyLoading.value"
      :current-job-id="generator.currentJobId.value"
      empty-hint="输入提示词后点击「生成视频」开始第一次自由生视频"
      unit="个"
      @close="closeHistoryDrawer"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="zoomCard"
      title="自由生视频预览"
      alt="自由生视频预览"
      media-type="video"
      @close="closePreview"
    />
  </GeneratorLayout>
</template>
