<script setup>
import { computed } from "vue";
import { LoaderCircle, WandSparkles } from "lucide-vue-next";
import GeneratorActionFooter from "@/components/generation/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/GeneratorSidePanelShell.vue";
import ImageUploader from "@/components/generation/ImageUploader.vue";
import ModuleSelector from "@/components/product-image/ModuleSelector.vue";
import ProductGenerationBasics from "@/components/generation/ProductGenerationBasics.vue";
import { availableModules } from "@/constants/generator.js";

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
  selectedModules: {
    type: Array,
    required: true,
  },
  aiLoading: {
    type: Boolean,
    default: false,
  },
  canGenerate: {
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
  selectedImageLabel: {
    type: String,
    required: true,
  },
  generateSellingPoints: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits([
  "update:settings",
  "update:uploadedImages",
  "update:mainImageIndex",
  "update:selectedModules",
  "notify",
  "generate",
]);

const hasGenerationSource = computed(
  () => props.uploadedImages.length > 0 && props.settings.productInput.trim().length > 0,
);
const generateButtonText = computed(() => {
  if (!hasGenerationSource.value) return "请先上传产品图并填写商品卖点与要求";
  if (props.selectedModules.length === 0) return "请至少选择一个生成图种";
  if (props.strategyLoading) return "AI 正在生成模块策略...";
  if (props.generating) return `AI 高端排版中... (${props.generatedCount}/${props.selectedModules.length})`;
  return `立即生成模块策略 (${props.selectedModules.length}项)`;
});

</script>

<template>
  <GeneratorSidePanelShell>
    <ImageUploader
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

    <ModuleSelector
      :selected="selectedModules"
      :modules="availableModules"
      @update:selected="emit('update:selectedModules', $event)"
    />

    <template #footer>
      <GeneratorActionFooter
        :primary-text="generateButtonText"
        :primary-disabled="!canGenerate"
        @primary="emit('generate')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="generating || strategyLoading" class="h-4 w-4 animate-spin" />
          <WandSparkles v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
