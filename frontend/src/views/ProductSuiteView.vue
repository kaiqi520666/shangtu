<script setup>
import AppModal from '@/components/AppModal.vue'
import GeneratorLayout from '@/components/GeneratorLayout.vue'
import ProductSuiteSettingsPanel from '@/components/ProductSuiteSettingsPanel.vue'
import ProductSuiteWorkspace from '@/components/ProductSuiteWorkspace.vue'
import { useProductSuiteGenerator } from '@/composables/useProductSuiteGenerator.js'

const suite = useProductSuiteGenerator()
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
      :selected-image-label="suite.selectedImageLabel.value"
      :generate-selling-points="suite.generateSellingPointsWithAI"
      @update:settings="Object.assign(suite.settings, $event)"
      @update:uploaded-images="suite.uploadedImages.value = $event"
      @update:main-image-index="suite.mainImageIndex.value = $event"
      @update:suite-structure="suite.suiteStructure.value = $event"
      @notify="suite.showNotice"
      @generate="suite.generateSuiteImages"
    />

    <ProductSuiteWorkspace
      :settings="suite.settings"
      :current-task-title="suite.currentTaskTitle.value"
      :output-cards="suite.outputCards.value"
      :generating="suite.generating.value"
      :generated-count="suite.generatedCount.value"
      :total-count="suite.totalCount.value"
      :gen-logs="suite.genLogs.value"
      :selected-cards-count="suite.selectedCardsCount.value"
      :selected-image-label="suite.selectedImageLabel.value"
      :get-structure-name="suite.getStructureName"
      :get-structure-strategy="suite.getStructureStrategy"
      @update:current-task-title="suite.currentTaskTitle.value = $event"
      @select-all-cards="suite.toggleSelectAllCards"
      @batch-download="suite.batchDownload"
      @toggle-card="suite.toggleCardSelection"
      @download-card="suite.downloadSingleImage"
      @regenerate-card="suite.regenerateSingleCard"
      @zoom-card="suite.zoomCard.value = $event"
    />

    <AppModal
      :open="Boolean(suite.zoomCard.value)"
      title="商品套图大图预览"
      panel-class="w-full max-w-4xl"
      @close="suite.zoomCard.value = null"
    >
      <div v-if="suite.zoomCard.value" class="bg-slate-100 p-6">
        <img :src="suite.zoomCard.value.dataUrl" class="mx-auto max-h-[75vh] rounded-xl object-contain shadow-lg" alt="商品套图预览" />
      </div>
    </AppModal>
  </GeneratorLayout>
</template>
