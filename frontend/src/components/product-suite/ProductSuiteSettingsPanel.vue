<script setup>
import { computed } from 'vue'
import { LoaderCircle, Sparkles } from 'lucide-vue-next'
import GeneratorActionFooter from '@/components/generation/GeneratorActionFooter.vue'
import GeneratorSidePanelShell from '@/components/generation/GeneratorSidePanelShell.vue'
import ImageUploader from '@/components/generation/ImageUploader.vue'
import ProductGenerationBasics from '@/components/generation/ProductGenerationBasics.vue'
import SuiteStructureConfigurator from '@/components/product-suite/SuiteStructureConfigurator.vue'

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  uploadedImages: {
    type: Array,
    required: true,
  },
  mainImageIndex: {
    type: Number,
    required: true,
  },
  suiteStructure: {
    type: Array,
    required: true,
  },
  aiLoading: {
    type: Boolean,
    default: false,
  },
  canGenerateStrategy: {
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
  generating: {
    type: Boolean,
    default: false,
  },
  strategyLoading: {
    type: Boolean,
    default: false,
  },
  generatedCount: {
    type: Number,
    default: 0,
  },
  totalCount: {
    type: Number,
    default: 0,
  },
  jobTotal: {
    type: Number,
    default: 0,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  generateSellingPoints: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'update:settings',
  'update:uploadedImages',
  'update:mainImageIndex',
  'update:suiteStructure',
  'notify',
  'generate-strategy',
])

const primaryText = computed(() => {
  if (props.uploadedImages.length === 0) return '请先上传商品图片'
  if (!props.settings.productInput.trim()) return '请填写商品卖点与要求'
  if (props.totalCount === 0) return '请至少选择一个套图类型'
  if (props.strategyLoading) return 'AI 正在生成策略...'
  if (props.hasRunningTasks) return '生成中暂不可改策略'
  if (props.creatingBatch) return '正在创建任务...'
  return `AI 生成套图策略（${props.totalCount}张）`
})
</script>

<template>
  <GeneratorSidePanelShell>
    <ImageUploader
      title="商品套图"
      add-text="添加商品图"
      hint-text="拖拽或点击"
      alt-text="商品"
      limit-message="最多只能上传 3 张商品图"
      :images="uploadedImages"
      :main-index="mainImageIndex"
      @update:images="emit('update:uploadedImages', $event)"
      @update:main-index="emit('update:mainImageIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <ProductGenerationBasics
      :settings="settings"
      :ai-loading="aiLoading"
      :selected-image-label="selectedImageLabel"
      :generate-selling-points="generateSellingPoints"
      @update:settings="emit('update:settings', $event)"
    />

    <SuiteStructureConfigurator
      :structure="suiteStructure"
      @update:structure="emit('update:suiteStructure', $event)"
    />

    <template #footer>
      <GeneratorActionFooter
        :primary-text="primaryText"
        :primary-disabled="!canGenerateStrategy"
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
