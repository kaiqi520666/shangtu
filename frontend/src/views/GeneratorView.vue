<script setup>
import GeneratorLayout from '@/components/GeneratorLayout.vue'
import GeneratorOverlays from '@/components/GeneratorOverlays.vue'
import GeneratorSettingsPanel from '@/components/GeneratorSettingsPanel.vue'
import GeneratorWorkspace from '@/components/GeneratorWorkspace.vue'
import StrategyReviewPanel from '@/components/StrategyReviewPanel.vue'
import { useGenerator } from '@/composables/useGenerator.js'

const generator = useGenerator()
</script>

<template>
  <GeneratorLayout
    :task-count="generator.taskQueue.value.length"
    @open-queue="generator.showQueueDrawer.value = true"
    @open-history="generator.showHistoryDrawer.value = true"
  >
    <StrategyReviewPanel
      v-if="generator.strategyPanelVisible.value"
      placement="side"
      :loading="generator.strategyLoading.value"
      :brief="generator.strategyBrief.value"
      :modules="generator.moduleContents.value"
      :settings="generator.settings"
      :selected-image-label="generator.selectedImageLabel.value"
      @back="generator.backToConfig"
      @confirm="generator.confirmStrategyAndGenerate"
      @update-module="generator.updateModuleContent"
      @reorder-modules="generator.reorderModuleContents"
      @remove-module="generator.removeModuleContent"
    />

    <GeneratorSettingsPanel
      v-else
      :settings="generator.settings"
      :uploaded-images="generator.uploadedImages.value"
      :main-image-index="generator.mainImageIndex.value"
      :selected-modules="generator.selectedModules.value"
      :ai-loading="generator.aiLoading.value"
      :can-generate="generator.canGenerate.value"
      :generating="generator.generating.value"
      :strategy-loading="generator.strategyLoading.value"
      :generated-count="generator.generatedCount.value"
      :selected-image-label="generator.selectedImageLabel.value"
      :generate-selling-points="generator.generateSellingPointsWithAI"
      @update:settings="Object.assign(generator.settings, $event)"
      @update:uploaded-images="generator.uploadedImages.value = $event"
      @update:main-image-index="generator.mainImageIndex.value = $event"
      @update:selected-modules="generator.selectedModules.value = $event"
      @notify="generator.showNotice"
      @generate="generator.triggerStrategyGeneration"
    />

    <GeneratorWorkspace
      :settings="generator.settings"
      :current-task-title="generator.currentTaskTitle.value"
      :output-cards="generator.outputCards.value"
      :generating="generator.generating.value"
      :generated-count="generator.generatedCount.value"
      :selected-modules="generator.selectedModules.value"
      :gen-logs="generator.genLogs.value"
      :selected-cards-count="generator.selectedCardsCount.value"
      :generation-progress-class="generator.generationProgressClass.value"
      :selected-image-label="generator.selectedImageLabel.value"
      :get-module-name="generator.getModuleName"
      :get-module-strategy="generator.getModuleStrategy"
      @update:current-task-title="generator.currentTaskTitle.value = $event"
      @select-all-cards="generator.toggleSelectAllCards"
      @preview-long-image="generator.previewLongImage"
      @batch-download="generator.batchDownload"
      @toggle-card="generator.toggleCardSelection"
      @download-card="generator.downloadSingleImage"
      @regenerate-card="generator.regenerateSingleCard"
      @zoom-card="generator.zoomCard.value = $event"
    />

    <GeneratorOverlays
      :show-long-preview-modal="generator.showLongPreviewModal.value"
      :show-history-drawer="generator.showHistoryDrawer.value"
      :show-queue-drawer="generator.showQueueDrawer.value"
      :zoom-card="generator.zoomCard.value"
      :selected-cards="generator.selectedCards.value"
      :selected-cards-count="generator.selectedCardsCount.value"
      :long-preview-height="generator.longPreviewHeight.value"
      :history-tasks="generator.historyTasks.value"
      :task-queue="generator.taskQueue.value"
      :get-module-name="generator.getModuleName"
      :get-module-strategy="generator.getModuleStrategy"
      :get-progress-width-class="generator.getProgressWidthClass"
      @close-long-preview="generator.showLongPreviewModal.value = false"
      @download-long-image="generator.downloadLongCombinedImage"
      @close-history="generator.showHistoryDrawer.value = false"
      @load-history="generator.loadHistoryTask"
      @close-queue="generator.showQueueDrawer.value = false"
      @close-zoom="generator.zoomCard.value = null"
    />
  </GeneratorLayout>
</template>
