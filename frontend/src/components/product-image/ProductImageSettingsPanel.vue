<script setup>
import { computed } from "vue";
import { LoaderCircle, Sparkles, WandSparkles } from "lucide-vue-next";
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
  aiLoading: {
    type: Boolean,
    default: false,
  },
  canGenerate: {
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
  "generate-strategy",
]);

const hasGenerationSource = computed(
  () => props.uploadedImages.length > 0 && props.settings.productInput.trim().length > 0,
);
const generateButtonText = computed(() => {
  if (!hasGenerationSource.value) return "请先上传产品图并填写商品卖点与要求";
  if (props.catalogLoading) return "图种目录加载中...";
  if (props.selectedModules.length === 0) return "请至少选择一个生成图种";
  if (props.creatingBatch) return "正在创建任务...";
  if (props.hasRunningTasks) return `追加生成详情图 (${props.selectedModules.length}项)`;
  return `生成详情图 (${props.selectedModules.length}项)`;
});

const strategyButtonText = computed(() => {
  if (props.strategyLoading) return "AI 正在生成策略...";
  if (props.catalogLoading) return "图种目录加载中...";
  if (props.hasRunningTasks) return "生成中暂不可改策略";
  return "AI 生成策略";
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
      :modules="modules"
      @update:selected="emit('update:selectedModules', $event)"
    />

    <section class="border-t border-slate-100 p-5">
      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-xl border border-primary/20 bg-primary/5 px-4 py-2.5 text-xs font-bold text-primary transition-colors hover:border-primary/40 hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="!canGenerateStrategy"
        @click="emit('generate-strategy')"
      >
        <LoaderCircle v-if="strategyLoading" class="h-4 w-4 animate-spin" />
        <Sparkles v-else class="h-4 w-4" />
        {{ strategyButtonText }}
      </button>
    </section>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="generateButtonText"
        :primary-disabled="!canGenerate"
        @primary="emit('generate')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="creatingBatch" class="h-4 w-4 animate-spin" />
          <WandSparkles v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
