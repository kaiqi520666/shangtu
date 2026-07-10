<script setup>
import { computed } from 'vue'
import { LoaderCircle, Sparkles } from 'lucide-vue-next'
import GeneratorActionFooter from '@/components/generation/workspace/GeneratorActionFooter.vue'
import GeneratorSidePanelShell from '@/components/generation/workspace/GeneratorSidePanelShell.vue'
import ImageUploader from '@/components/generation/image/ImageUploader.vue'
import ProductGenerationBasics from '@/components/generation/workspace/ProductGenerationBasics.vue'
import ModelSelector from '@/components/outfit/ModelSelector.vue'
import ScenePresetSelector from '@/components/outfit/ScenePresetSelector.vue'

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
  scenes: {
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
  creatingBatch: {
    type: Boolean,
    default: false,
  },
  hasRunningTasks: {
    type: Boolean,
    default: false,
  },
  canGenerateStrategy: {
    type: Boolean,
    default: false,
  },
  strategyLoading: {
    type: Boolean,
    default: false,
  },
  catalogLoading: {
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
  'generate-strategy',
])

const primaryText = computed(() => {
  if (props.garmentImages.length === 0) return '请先上传服装图片'
  if (!props.selectedModelId) return '请选择模特形象'
  if (props.catalogLoading) return '场景目录加载中...'
  if (props.selectedScenes.length === 0) return '请至少选择一个拍摄场景'
  if (props.strategyLoading) return 'AI 正在生成策略...'
  if (props.hasRunningTasks) return '生成中暂不可改策略'
  if (props.creatingBatch) return '正在创建任务...'
  return `AI 生成穿搭策略（${props.selectedScenes.length}张）`
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
      :scenes="scenes"
      :selected="selectedScenes"
      :description="sceneDescription"
      @update:selected="emit('update:selectedScenes', $event)"
      @update:description="emit('update:sceneDescription', $event)"
    />

    <template #footer>
      <GeneratorActionFooter
        :primary-text="primaryText"
        :primary-disabled="modelsLoading || catalogLoading || !canGenerateStrategy"
        @primary="emit('generate-strategy')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="strategyLoading || creatingBatch" class="h-4 w-4 animate-spin" />
          <Sparkles v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
