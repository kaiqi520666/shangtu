<script setup>
import AppModal from '@/components/ui/AppModal.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import OutfitSceneReviewPanel from '@/components/outfit/OutfitSceneReviewPanel.vue'
import OutfitSettingsPanel from '@/components/outfit/OutfitSettingsPanel.vue'
import OutfitWorkspace from '@/components/outfit/OutfitWorkspace.vue'
import { useOutfitGenerator } from '@/composables/useOutfitGenerator.js'

const outfit = useOutfitGenerator()
</script>

<template>
  <GeneratorLayout>
    <OutfitSceneReviewPanel
      v-if="outfit.workflowStep.value === 'scene-loading' || outfit.workflowStep.value === 'scene-review'"
      :loading="outfit.loadingScenes.value"
      :poses="outfit.recommendedPoses.value"
      :selected-count="outfit.selectedPoseCount.value"
      @back="outfit.backToConfig"
      @generate-images="outfit.generateOutfitImages"
      @toggle-pose="outfit.togglePose"
      @update-pose="outfit.updatePose"
    />

    <OutfitSettingsPanel
      v-else
      :garment-images="outfit.garmentImages.value"
      :main-garment-index="outfit.mainGarmentIndex.value"
      :models="outfit.modelLibrary.value"
      :models-loading="outfit.modelsLoading.value"
      :selected-model-id="outfit.selectedModelId.value"
      :selected-scenes="outfit.selectedScenes.value"
      :scene-description="outfit.sceneDescription.value"
      :ratio="outfit.ratio.value"
      :loading="outfit.loadingScenes.value"
      :can-generate="outfit.canGenerateScenes.value"
      @update:garment-images="outfit.garmentImages.value = $event"
      @update:main-garment-index="outfit.mainGarmentIndex.value = $event"
      @update:selected-model-id="outfit.selectedModelId.value = $event"
      @update:selected-scenes="outfit.selectedScenes.value = $event"
      @update:scene-description="outfit.sceneDescription.value = $event"
      @update:ratio="outfit.ratio.value = $event"
      @notify="outfit.showNotice"
      @generate-scenes="outfit.generateRecommendedScenes"
    />

    <OutfitWorkspace
      :current-task-title="outfit.currentTaskTitle.value"
      :preview-slides="outfit.previewSlides.value"
      :output-cards="outfit.outputCards.value"
      :generating="outfit.generating.value"
      :generated-count="outfit.generatedCount.value"
      :selected-pose-count="outfit.selectedPoseCount.value"
      :gen-logs="outfit.genLogs.value"
      :selected-image-label="outfit.selectedImageLabel.value"
      :settings="outfit.settings"
      :get-pose-name="outfit.getPoseName"
      :get-pose-strategy="outfit.getPoseStrategy"
      @update:current-task-title="outfit.currentTaskTitle.value = $event"
      @select-all-cards="outfit.toggleSelectAllCards"
      @toggle-card="outfit.toggleCardSelection"
      @download-card="outfit.downloadSingleImage"
      @regenerate-card="outfit.regenerateSingleCard"
      @zoom-card="outfit.zoomCard.value = $event"
    />

    <AppModal
      :open="Boolean(outfit.zoomCard.value)"
      title="服饰穿搭大图预览"
      panel-class="w-full max-w-4xl"
      @close="outfit.zoomCard.value = null"
    >
      <div v-if="outfit.zoomCard.value" class="bg-slate-100 p-6">
        <img :src="outfit.zoomCard.value.dataUrl" class="mx-auto max-h-[75vh] rounded-xl object-contain shadow-lg" alt="服饰穿搭预览" />
      </div>
    </AppModal>
  </GeneratorLayout>
</template>
