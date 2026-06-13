<script setup>
import { computed } from 'vue'
import { LoaderCircle, RectangleVertical, Smartphone, Square, WandSparkles } from 'lucide-vue-next'
import GeneratorActionFooter from '@/components/generation/GeneratorActionFooter.vue'
import GeneratorSidePanelShell from '@/components/generation/GeneratorSidePanelShell.vue'
import ImageUploader from '@/components/generation/ImageUploader.vue'
import ModelSelector from '@/components/outfit/ModelSelector.vue'
import ScenePresetSelector from '@/components/outfit/ScenePresetSelector.vue'
import { outfitRatioOptions, scenePresets } from '@/constants/outfit.js'

const props = defineProps({
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
  ratio: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  canGenerate: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:garmentImages',
  'update:mainGarmentIndex',
  'update:selectedModelId',
  'update:selectedScenes',
  'update:sceneDescription',
  'update:ratio',
  'notify',
  'generate-scenes',
])

const primaryText = computed(() => {
  if (props.modelsLoading) return '正在加载模特...'
  if (!props.canGenerate) return '请上传服装图并选择模特'
  if (props.loading) return '正在生成推荐场景...'
  return '生成推荐场景'
})

const ratioIconMap = {
  '3:4': RectangleVertical,
  '1:1': Square,
  '9:16': Smartphone,
}
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
      :selected-id="selectedModelId"
      @update:selected-id="emit('update:selectedModelId', $event)"
    />

    <ScenePresetSelector
      :scenes="scenePresets"
      :selected="selectedScenes"
      :description="sceneDescription"
      @update:selected="emit('update:selectedScenes', $event)"
      @update:description="emit('update:sceneDescription', $event)"
    />

    <section class="space-y-3 p-5">
      <h3 class="text-xs font-bold text-slate-900">图片比例</h3>
      <div class="grid grid-cols-3 gap-2 rounded-xl bg-slate-100 p-1">
        <button
          v-for="option in outfitRatioOptions"
          :key="option.value"
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold transition-colors"
          :class="ratio === option.value ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-800'"
          @click="emit('update:ratio', option.value)"
        >
          <component :is="ratioIconMap[option.value]" class="h-3.5 w-3.5" />
          {{ option.label }}
        </button>
      </div>
    </section>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="primaryText"
        :primary-disabled="modelsLoading || !canGenerate"
        @primary="emit('generate-scenes')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
          <WandSparkles v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
