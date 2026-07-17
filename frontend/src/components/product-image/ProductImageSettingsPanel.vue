<script setup>
import { computed } from "vue";
import { LoaderCircle, Sparkles } from "lucide-vue-next";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import ImageUploader from "@/components/generation/image/ImageUploader.vue";
import ModuleSelector from "@/components/product-image/ModuleSelector.vue";
import ProductGenerationBasics from "@/components/generation/workspace/ProductGenerationBasics.vue";

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
  modules: {
    type: Array,
    required: true,
  },
  catalogLoading: {
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
  strategyLoading: {
    type: Boolean,
    default: false,
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
  "generate-strategy",
]);

const hasGenerationSource = computed(
  () => props.uploadedImages.length > 0 && props.settings.productInput.trim().length > 0,
);
const primaryText = computed(() => {
  if (!hasGenerationSource.value) return "请先上传产品图并填写商品卖点与要求";
  if (props.catalogLoading) return "图种目录加载中...";
  if (props.selectedModules.length === 0) return "请至少选择一个生成图种";
  if (props.strategyLoading) return "AI 正在生成方案...";
  if (props.hasRunningTasks) return "生成中暂不可改方案";
  if (props.creatingBatch) return "正在创建任务...";
  return `生成详情图方案（${props.selectedModules.length}张）`;
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
      :selected-image-label="selectedImageLabel"
      :generate-selling-points="generateSellingPoints"
      @update:settings="emit('update:settings', $event)"
    />

    <ModuleSelector
      :selected="selectedModules"
      :modules="modules"
      @update:selected="emit('update:selectedModules', $event)"
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
