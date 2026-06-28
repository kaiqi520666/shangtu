<script setup>
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/image/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/workspace/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/workspace/GenerationPreviewModal.vue'
import GenerationWorkspace from '@/components/generation/workspace/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import FreeImageSettingsPanel from '@/components/free-image/FreeImageSettingsPanel.vue'
import { useGeneratorCardEdit } from '@/composables/generator/useGeneratorCardEdit.js'
import { useGeneratorRouteJob } from '@/composables/generator/restore/useGeneratorRouteJob.js'
import { useFreeImageGenerator } from '@/composables/generator/useFreeImageGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const generator = useFreeImageGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/free-image/${jobId}`)
  },
})

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator,
  route,
  router,
  basePath: '/generator/free-image',
  toast,
  confirm,
})

const {
  editModalOpen,
  editCard,
  editSubmitting,
  openEditModal,
  closeEditModal,
  handleRegenerate,
  handleDeleteCardDirect,
} = useGeneratorCardEdit({
  generator,
  toast,
  confirm,
  afterRegenerateCardUpdate(target, prompt) {
    target.strategyContent = prompt
  },
})

function closeHistoryDrawer() {
  generator.showHistoryDrawer.value = false
}

function openPreview(card) {
  generator.zoomCard.value = card
}

function closePreview() {
  generator.zoomCard.value = null
}
</script>

<template>
  <GeneratorLayout>
    <FreeImageSettingsPanel
      :settings="generator.settings"
      :reference-images="generator.referenceImages.value"
      :main-image-index="generator.mainImageIndex.value"
      :optimizing="generator.optimizing.value"
      :can-optimize="generator.canOptimize.value"
      :can-generate="generator.canGenerate.value"
      :creating-batch="generator.creatingBatch.value"
      :has-running-tasks="generator.hasRunningTasks.value"
      :generating="generator.generating.value"
      :generated-count="generator.generatedCount.value"
      :total-count="generator.totalCount.value"
      :job-total="generator.jobTotal.value"
      :selected-image-label="generator.selectedImageLabel.value"
      @update:settings="Object.assign(generator.settings, $event)"
      @update:reference-images="generator.referenceImages.value = $event"
      @update:main-image-index="generator.mainImageIndex.value = $event"
      @notify="generator.showNotice"
      @optimize="generator.optimizePrompt"
      @generate="generator.generateFreeImage"
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
      :total-count="generator.totalCount.value"
      :job-total="generator.jobTotal.value"
      :gen-logs="generator.genLogs.value"
      :selected-cards-count="generator.selectedCardsCount.value"
      :selected-image-label="generator.selectedImageLabel.value"
      :get-module-name="generator.getModuleName"
      title-badge="本次自由生图"
      empty-title="自由生图"
      empty-subtitle="输入提示词，可选参考图，直接生成你想要的画面。"
      loading-title="AI 自由生图生成中"
      progress-text="正在生成自由生图"
      @update:current-task-title="generator.updateCurrentJobTitle"
      @select-all-cards="generator.toggleSelectAllCards"
      @batch-download="generator.batchDownload"
      @toggle-card="generator.toggleCardSelection"
      @download-card="generator.downloadSingleImage"
      @edit-card="openEditModal"
      @zoom-card="openPreview"
      @delete-card="handleDeleteCardDirect"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="generator.showHistoryDrawer.value"
      :jobs="generator.historyTasks.value"
      :loading="generator.historyLoading.value"
      :current-job-id="generator.currentJobId.value"
      empty-hint="输入提示词后点击「生成图片」开始第一次自由生图"
      @close="closeHistoryDrawer"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="generator.zoomCard.value"
      title="自由生图大图预览"
      alt="自由生图预览"
      @close="closePreview"
    />

    <ImageEditModal
      :open="editModalOpen"
      :card="editCard"
      module-name="自由生图"
      :submitting="editSubmitting"
      @close="closeEditModal"
      @submit="handleRegenerate"
      @delete="handleDeleteCardDirect(editCard)"
    />
  </GeneratorLayout>
</template>
