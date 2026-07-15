<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import VideoTranslationSettingsPanel from "@/components/video-translation/VideoTranslationSettingsPanel.vue";
import GenerationHistoryDrawer from "@/components/generation/workspace/GenerationHistoryDrawer.vue";
import GenerationPreviewModal from "@/components/generation/workspace/GenerationPreviewModal.vue";
import GenerationWorkspace from "@/components/generation/workspace/GenerationWorkspace.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import { useVideoTranslationGenerator } from "@/composables/generator/useVideoTranslationGenerator.js";
import { useGeneratorRouteJob } from "@/composables/generator/restore/useGeneratorRouteJob.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

const route = useRoute();
const router = useRouter();
const confirm = useConfirm();
const toast = useToast();
const videoTranslation = useVideoTranslationGenerator({
  toast,
  confirm,
  onJobCreated(jobId) {
    router.replace(`/generator/video-translation/${jobId}`);
  },
});
const zoomCard = ref(null);

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator: videoTranslation,
  route,
  router,
  basePath: "/generator/video-translation",
  toast,
  confirm,
  deleteMessage: "确定删除这个视频翻译任务吗？已生成视频不会立即从存储中物理删除。",
});

function openPreview(card) {
  if (card.status !== "done" || !card.dataUrl) return;
  zoomCard.value = card;
}

function closePreview() {
  zoomCard.value = null;
}

function closeHistoryDrawer() {
  videoTranslation.showHistoryDrawer.value = false;
}

onMounted(() => {
  videoTranslation.loadConfig();
});
</script>

<template>
  <GeneratorLayout>
    <VideoTranslationSettingsPanel
      :settings="videoTranslation.settings"
      :selected-video="videoTranslation.selectedVideo.value"
      :language-options="videoTranslation.languageOptions.value"
      :quality-options="videoTranslation.qualityOptions.value"
      :fee-text="videoTranslation.feeText.value"
      :generate-disabled="!videoTranslation.canGenerate.value"
      :generate-text="videoTranslation.generateButtonText.value"
      @update:settings="videoTranslation.updateSettings"
      @update:selected-video="videoTranslation.selectedVideo.value = $event"
      @generate="videoTranslation.generateVideoTranslation"
      @notify="videoTranslation.showNotice"
    />

    <GenerationWorkspace
      :settings="videoTranslation.settings"
      :current-task-title="videoTranslation.currentTaskTitle.value"
      :output-cards="videoTranslation.outputCards.value"
      :generating="videoTranslation.generating.value"
      :creating-batch="videoTranslation.creatingBatch.value"
      :generated-count="videoTranslation.generatedCount.value"
      :running-count="videoTranslation.runningCount.value"
      :failed-count="videoTranslation.failedCount.value"
      :total-count="videoTranslation.jobTotal.value"
      :job-total="videoTranslation.jobTotal.value"
      :gen-logs="videoTranslation.genLogs.value"
      :selected-cards-count="videoTranslation.selectedCardsCount.value"
      :downloading="videoTranslation.downloading.value"
      selected-image-label="翻译视频"
      :get-module-name="videoTranslation.getVideoTranslationModuleName"
      empty-title="视频翻译工作台"
      empty-subtitle="上传视频并选择目标语言后，这里会显示翻译进度和结果。"
      empty-image="https://image.nodepass.net/generated/2/2026/07/dac9ec6dcf6c415bab6f2cd107e3b604.png"
      empty-image-alt="同一主持人的双语视频翻译效果"
      media-type="video"
      media-unit="个"
      loading-title="视频翻译中"
      loading-description="正在提交 HeyGen 翻译任务，稍后会在这里显示状态和成片结果。"
      progress-text="正在翻译视频"
      @update:current-task-title="videoTranslation.updateCurrentJobTitle"
      @select-all-cards="videoTranslation.toggleSelectAllCards"
      @batch-download="videoTranslation.batchDownload"
      @toggle-card="videoTranslation.toggleCardSelection"
      @download-card="videoTranslation.downloadSingleVideo"
      @zoom-card="openPreview"
      @delete-card="videoTranslation.removeCard"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="videoTranslation.showHistoryDrawer.value"
      :jobs="videoTranslation.historyTasks.value"
      :loading="videoTranslation.historyLoading.value"
      :current-job-id="videoTranslation.currentJobId.value"
      empty-hint="点击「新建任务」开始视频翻译"
      unit="个"
      @close="closeHistoryDrawer"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="zoomCard"
      title="翻译视频预览"
      alt="翻译视频预览"
      media-type="video"
      @close="closePreview"
    />
  </GeneratorLayout>
</template>
