<script setup>
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/GenerationPreviewModal.vue'
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import OutfitSettingsPanel from '@/components/outfit/OutfitSettingsPanel.vue'
import OutfitStrategyReviewPanel from '@/components/outfit/OutfitStrategyReviewPanel.vue'
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

async function handleDeleteModel(modelId) {
  const ok = await confirm.open({
    title: '删除模特',
    message: '删除后该模特不会再出现在你的服饰穿搭模特列表中。',
    confirmText: '删除',
    tone: 'danger',
  })
  if (!ok) return
  await outfit.deleteModel(modelId)
}
</script>

<template>
  <GeneratorLayout>
    <OutfitStrategyReviewPanel
      v-if="outfit.strategyPanelVisible.value"
      placement="side"
      :loading="outfit.strategyLoading.value"
      :brief="outfit.strategyBrief.value"
      :items="outfit.outfitStrategyItems.value"
      :settings="outfit.settings"
      :selected-image-label="outfit.selectedImageLabel.value"
      :dirty="outfit.strategyDirty.value"
      @back="outfit.backToConfig"
      @confirm="outfit.confirmStrategyAndGenerate"
      @update-item="outfit.updateOutfitStrategyItem"
      @reorder-items="outfit.reorderOutfitStrategyItems"
      @remove-item="outfit.removeOutfitStrategyItem"
    />

    <OutfitSettingsPanel
      v-else
      :settings="outfit.settings"
      :garment-images="outfit.garmentImages.value"
      :main-garment-index="outfit.mainGarmentIndex.value"
      :models="outfit.modelLibrary.value"
      :models-loading="outfit.modelsLoading.value"
      :model-uploading="outfit.modelUploading.value"
      :model-deleting-id="outfit.modelDeletingId.value"
      :selected-model-id="outfit.selectedModelId.value"
      :selected-scenes="outfit.selectedScenes.value"
      :scenes="outfit.outfitScenes.value"
      :catalog-loading="outfit.catalogLoading.value"
      :scene-description="outfit.sceneDescription.value"
      :selected-image-label="outfit.selectedImageLabel.value"
      :loading="outfit.generating.value"
      :creating-batch="outfit.creatingBatch.value"
      :has-running-tasks="outfit.hasRunningTasks.value"
      :can-generate-strategy="outfit.canGenerateStrategy.value"
      :strategy-loading="outfit.strategyLoading.value"
      @update:settings="Object.assign(outfit.settings, $event)"
      @update:garment-images="outfit.garmentImages.value = $event"
      @update:main-garment-index="outfit.mainGarmentIndex.value = $event"
      @update:selected-model-id="outfit.selectedModelId.value = $event"
      @update:selected-scenes="outfit.selectedScenes.value = $event"
      @update:scene-description="outfit.sceneDescription.value = $event"
      @notify="outfit.showNotice"
      @upload-model="outfit.uploadModel"
      @delete-model="handleDeleteModel"
      @generate-strategy="outfit.triggerStrategyGeneration"
    />

    <GenerationWorkspace
      :settings="outfit.settings"
      :current-task-title="outfit.currentTaskTitle.value"
      :output-cards="outfit.outputCards.value"
      :generating="outfit.generating.value"
      :creating-batch="outfit.creatingBatch.value"
      :generated-count="outfit.generatedCount.value"
      :running-count="outfit.runningCount.value"
      :failed-count="outfit.failedCount.value"
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
