<script setup>
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/GenerationPreviewModal.vue'
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import OutfitSettingsPanel from '@/components/outfit/OutfitSettingsPanel.vue'
import { useGeneratorCardEdit } from '@/composables/useGeneratorCardEdit.js'
import { useGeneratorRouteJob } from '@/composables/useGeneratorRouteJob.js'
import { useOutfitGenerator } from '@/composables/useOutfitGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const outfit = useOutfitGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/outfit/${jobId}`)
  },
})

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator: outfit,
  route,
  router,
  basePath: '/generator/outfit',
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
  handleDeleteCard,
  handleDeleteCardDirect,
} = useGeneratorCardEdit({
  generator: outfit,
  toast,
  confirm,
})

function closeHistoryDrawer() {
  outfit.showHistoryDrawer.value = false
}

function openPreview(card) {
  outfit.zoomCard.value = card
}

function closePreview() {
  outfit.zoomCard.value = null
}
</script>

<template>
  <GeneratorLayout>
    <OutfitSettingsPanel
      :settings="outfit.settings"
      :garment-images="outfit.garmentImages.value"
      :main-garment-index="outfit.mainGarmentIndex.value"
      :models="outfit.modelLibrary.value"
      :models-loading="outfit.modelsLoading.value"
      :selected-model-id="outfit.selectedModelId.value"
      :selected-scenes="outfit.selectedScenes.value"
      :scene-description="outfit.sceneDescription.value"
      :selected-image-label="outfit.selectedImageLabel.value"
      :loading="outfit.generating.value"
      :can-generate="outfit.canGenerate.value"
      @update:settings="Object.assign(outfit.settings, $event)"
      @update:garment-images="outfit.garmentImages.value = $event"
      @update:main-garment-index="outfit.mainGarmentIndex.value = $event"
      @update:selected-model-id="outfit.selectedModelId.value = $event"
      @update:selected-scenes="outfit.selectedScenes.value = $event"
      @update:scene-description="outfit.sceneDescription.value = $event"
      @notify="outfit.showNotice"
      @generate-images="outfit.generateOutfitImages"
    />

    <GenerationWorkspace
      :settings="outfit.settings"
      :current-task-title="outfit.currentTaskTitle.value"
      :output-cards="outfit.outputCards.value"
      :generating="outfit.generating.value"
      :generated-count="outfit.generatedCount.value"
      :total-count="outfit.totalCount.value"
      :job-total="outfit.jobTotal.value"
      :gen-logs="outfit.genLogs.value"
      :selected-cards-count="outfit.selectedCardsCount.value"
      :selected-image-label="outfit.selectedImageLabel.value"
      :get-module-name="outfit.getSceneName"
      title-badge="本次穿搭任务"
      empty-title="服饰穿搭"
      empty-subtitle="上传服装图，选择模特和拍摄场景，一次生成多张穿搭图。"
      :empty-slides="outfit.previewSlides.value"
      loading-title="AI 服饰穿搭图生成中"
      progress-text="正在生成服饰穿搭图"
      @update:current-task-title="outfit.updateCurrentJobTitle"
      @select-all-cards="outfit.toggleSelectAllCards"
      @batch-download="outfit.batchDownload"
      @toggle-card="outfit.toggleCardSelection"
      @download-card="outfit.downloadSingleImage"
      @edit-card="openEditModal"
      @zoom-card="openPreview"
      @delete-card="handleDeleteCardDirect"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="outfit.showHistoryDrawer.value"
      :jobs="outfit.historyTasks.value"
      :loading="outfit.historyLoading.value"
      :current-job-id="outfit.currentJobId.value"
      @close="closeHistoryDrawer"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="outfit.zoomCard.value"
      title="服饰穿搭大图预览"
      alt="服饰穿搭预览"
      @close="closePreview"
    />

    <ImageEditModal
      :open="editModalOpen"
      :card="editCard"
      :module-name="editCard ? outfit.getSceneName(editCard.typeId) : ''"
      :submitting="editSubmitting"
      @close="closeEditModal"
      @submit="handleRegenerate"
      @delete="handleDeleteCard"
    />
  </GeneratorLayout>
</template>
