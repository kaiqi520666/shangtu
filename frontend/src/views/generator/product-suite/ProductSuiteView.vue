<script setup>
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/GenerationPreviewModal.vue'
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import ProductSuiteSettingsPanel from '@/components/product-suite/ProductSuiteSettingsPanel.vue'
import { useGeneratorCardEdit } from '@/composables/useGeneratorCardEdit.js'
import { useGeneratorRouteJob } from '@/composables/useGeneratorRouteJob.js'
import { useProductSuiteGenerator } from '@/composables/useProductSuiteGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'
import { productSuitePreviewSlides } from '@/constants/productSuite.js'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const suite = useProductSuiteGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/product-suite/${jobId}`)
  },
})

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator: suite,
  route,
  router,
  basePath: '/generator/product-suite',
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
  generator: suite,
  toast,
  confirm,
})
</script>

<template>
  <GeneratorLayout>
    <ProductSuiteSettingsPanel
      :settings="suite.settings"
      :uploaded-images="suite.uploadedImages.value"
      :main-image-index="suite.mainImageIndex.value"
      :suite-structure="suite.suiteStructure.value"
      :ai-loading="suite.aiLoading.value"
      :can-generate="suite.canGenerate.value"
      :generating="suite.generating.value"
      :generated-count="suite.generatedCount.value"
      :total-count="suite.totalCount.value"
      :job-total="suite.jobTotal.value"
      :selected-image-label="suite.selectedImageLabel.value"
      :generate-selling-points="suite.generateSellingPointsWithAI"
      @update:settings="Object.assign(suite.settings, $event)"
      @update:uploaded-images="suite.uploadedImages.value = $event"
      @update:main-image-index="suite.mainImageIndex.value = $event"
      @update:suite-structure="suite.suiteStructure.value = $event"
      @notify="suite.showNotice"
      @generate="suite.generateSuiteImages"
    />

    <GenerationWorkspace
      :settings="suite.settings"
      :current-task-title="suite.currentTaskTitle.value"
      :output-cards="suite.outputCards.value"
      :generating="suite.generating.value"
      :generated-count="suite.generatedCount.value"
      :total-count="suite.totalCount.value"
      :job-total="suite.jobTotal.value"
      :gen-logs="suite.genLogs.value"
      :selected-cards-count="suite.selectedCardsCount.value"
      :selected-image-label="suite.selectedImageLabel.value"
      :get-module-name="suite.getStructureName"
      title-badge="本次套图任务"
      empty-title="AI商品套图"
      empty-subtitle="上传商品图，AI 即刻生成符合多电商平台规范的高转化率商品套图。"
      :empty-slides="productSuitePreviewSlides"
      loading-title="AI 商品套图生成中"
      progress-text="正在生成商品套图"
      @update:current-task-title="suite.updateCurrentJobTitle"
      @select-all-cards="suite.toggleSelectAllCards"
      @batch-download="suite.batchDownload"
      @toggle-card="suite.toggleCardSelection"
      @download-card="suite.downloadSingleImage"
      @edit-card="openEditModal"
      @zoom-card="(card) => { suite.zoomCard.value = card }"
      @delete-card="handleDeleteCardDirect"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="suite.showHistoryDrawer.value"
      :jobs="suite.historyTasks.value"
      :loading="suite.historyLoading.value"
      :current-job-id="suite.currentJobId.value"
      @close="suite.showHistoryDrawer.value = false"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="suite.zoomCard.value"
      title="商品套图大图预览"
      alt="商品套图预览"
      @close="suite.zoomCard.value = null"
    />

    <ImageEditModal
      :open="editModalOpen"
      :card="editCard"
      :module-name="editCard ? suite.getStructureName(editCard.typeId) : ''"
      :submitting="editSubmitting"
      @close="closeEditModal"
      @submit="handleRegenerate"
      @delete="handleDeleteCard"
    />
  </GeneratorLayout>
</template>
