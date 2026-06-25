<script setup>
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/GenerationPreviewModal.vue'
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import ProductImageSettingsPanel from '@/components/product-image/ProductImageSettingsPanel.vue'
import StrategyReviewPanel from '@/components/product-image/StrategyReviewPanel.vue'
import { useGeneratorCardEdit } from '@/composables/useGeneratorCardEdit.js'
import { useGeneratorRouteJob } from '@/composables/useGeneratorRouteJob.js'
import { useProductImageGenerator } from '@/composables/useProductImageGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'
import { productDetailPreviewSlides } from '@/constants/generator.js'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const generator = useProductImageGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/product-image/${jobId}`)
  },
})

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator,
  route,
  router,
  basePath: '/generator/product-image',
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
  generator,
  toast,
  confirm,
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
    <StrategyReviewPanel
      v-if="generator.strategyPanelVisible.value"
      placement="side"
      :loading="generator.strategyLoading.value"
      :brief="generator.strategyBrief.value"
      :modules="generator.moduleContents.value"
      :settings="generator.settings"
      :selected-image-label="generator.selectedImageLabel.value"
      :dirty="generator.strategyDirty.value"
      @back="generator.backToConfig"
      @confirm="generator.confirmStrategyAndGenerate"
      @update-module="generator.updateModuleContent"
      @reorder-modules="generator.reorderModuleContents"
      @remove-module="generator.removeModuleContent"
    />

    <ProductImageSettingsPanel
      v-else
      :settings="generator.settings"
      :uploaded-images="generator.uploadedImages.value"
      :main-image-index="generator.mainImageIndex.value"
      :selected-modules="generator.selectedModules.value"
      :modules="generator.availableModules.value"
      :catalog-loading="generator.catalogLoading.value"
      :ai-loading="generator.aiLoading.value"
      :can-generate="generator.canGenerate.value"
      :can-generate-strategy="generator.canGenerateStrategy.value"
      :creating-batch="generator.creatingBatch.value"
      :has-running-tasks="generator.hasRunningTasks.value"
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
      @generate="generator.generateProductImages"
      @generate-strategy="generator.triggerStrategyGeneration"
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
      title-badge="本次详情图任务"
      empty-title="商品详情图"
      empty-subtitle="上传商品图，生成策略后输出多张电商详情页模块图。"
      :empty-slides="productDetailPreviewSlides"
      loading-title="AI 商品详情图生成中"
      progress-text="正在生成商品详情图"
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
      @close="closeHistoryDrawer"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="generator.zoomCard.value"
      title="商品详情图大图预览"
      alt="商品详情图预览"
      @close="closePreview"
    />

    <ImageEditModal
      :open="editModalOpen"
      :card="editCard"
      :module-name="editCard ? generator.getModuleName(editCard.typeId) : ''"
      :submitting="editSubmitting"
      @close="closeEditModal"
      @submit="handleRegenerate"
      @delete="handleDeleteCard"
    />
  </GeneratorLayout>
</template>
