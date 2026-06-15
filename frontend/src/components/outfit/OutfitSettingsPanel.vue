<script setup>
import { computed } from 'vue'
import { LoaderCircle, WandSparkles } from 'lucide-vue-next'
import GeneratorActionFooter from '@/components/generation/GeneratorActionFooter.vue'
import GeneratorSidePanelShell from '@/components/generation/GeneratorSidePanelShell.vue'
import ImageUploader from '@/components/generation/ImageUploader.vue'
import ProductGenerationBasics from '@/components/generation/ProductGenerationBasics.vue'
import ModelSelector from '@/components/outfit/ModelSelector.vue'
import ScenePresetSelector from '@/components/outfit/ScenePresetSelector.vue'
import { scenePresets } from '@/constants/outfit.js'

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  garmentImages: {
    type: Array,
    required: true,
  },
  mainGarmentIndex: {
    type: Number,
    required: true,
  },
  models: {
    type: Array,
    required: true,
  },
  modelsLoading: {
    type: Boolean,
    default: false,
  },
  modelUploading: {
    type: Boolean,
    default: false,
  },
  modelDeletingId: {
    type: String,
    default: '',
  },
  selectedModelId: {
    type: String,
    required: true,
  },
  selectedScenes: {
    type: Array,
    required: true,
  },
  sceneDescription: {
    type: String,
    default: '',
  },
  selectedImageLabel: {
    required: true,
    type: String,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  creatingBatch: {
    type: Boolean,
    default: false,
  },
  hasRunningTasks: {
    type: Boolean,
    default: false,
  },
  canGenerate: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:settings',
  'update:garmentImages',
  'update:mainGarmentIndex',
  'update:selectedModelId',
  'update:selectedScenes',
  'update:sceneDescription',
  'notify',
  'upload-model',
  'delete-model',
  'generate-images',
])

const primaryText = computed(() => {
  if (props.creatingBatch) return '正在创建任务...'
  if (props.hasRunningTasks) return '追加生成'
  return '生成图片'
})
</script>

<template>
  <GeneratorSidePanelShell>
    <ImageUploader
      title="服装图片"
      add-text="添加服装"
      hint-text="拖拽或点击"
      alt-text="服装"
      limit-message="最多只能上传 3 张服装图"
      :images="garmentImages"
      :main-index="mainGarmentIndex"
      @update:images="emit('update:garmentImages', $event)"
      @update:main-index="emit('update:mainGarmentIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <ModelSelector
      :models="models"
      :loading="modelsLoading"
      :uploading="modelUploading"
      :deleting-id="modelDeletingId"
      :selected-id="selectedModelId"
      @update:selected-id="emit('update:selectedModelId', $event)"
      @upload="emit('upload-model', $event)"
      @delete="emit('delete-model', $event)"
    />

    <ProductGenerationBasics
      :settings="settings"
      :selected-image-label="selectedImageLabel"
      :show-product-input="false"
      :show-ai-write="false"
      @update:settings="emit('update:settings', $event)"
    />

    <ScenePresetSelector
      :scenes="scenePresets"
      :selected="selectedScenes"
      :description="sceneDescription"
      @update:selected="emit('update:selectedScenes', $event)"
      @update:description="emit('update:sceneDescription', $event)"
    />

    <template #footer>
      <GeneratorActionFooter
        :primary-text="primaryText"
        :primary-disabled="modelsLoading || !canGenerate"
        @primary="emit('generate-images')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="creatingBatch" class="h-4 w-4 animate-spin" />
          <WandSparkles v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
