<script setup>
import { computed, watch } from "vue";
import { ImagePlus, LoaderCircle, Sparkles } from "lucide-vue-next";
import AppSelect from "@/components/ui/AppSelect.vue";
import ImageQualitySelector from "@/components/generation/image/ImageQualitySelector.vue";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorPanelSection from "@/components/generation/workspace/GeneratorPanelSection.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import ImageUploader from "@/components/generation/image/ImageUploader.vue";
import { ratioOptions, resolveQuality } from "@/constants/generator.js";

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  referenceImages: {
    type: Array,
    required: true,
  },
  mainImageIndex: {
    type: Number,
    required: true,
  },
  optimizing: {
    type: Boolean,
    default: false,
  },
  canOptimize: {
    type: Boolean,
    default: false,
  },
  canGenerate: {
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
  selectedImageLabel: {
    type: String,
    required: true,
  },
});

const emit = defineEmits([
  "update:settings",
  "update:referenceImages",
  "update:mainImageIndex",
  "notify",
  "optimize",
  "generate",
]);

const primaryText = computed(() => {
  if (!props.settings.prompt.trim()) return "请输入提示词";
  if (props.referenceImages.some((img) => img?.uploading)) return "参考图上传中...";
  if (props.creatingBatch) return "正在创建任务...";
  if (props.hasRunningTasks) return "追加生成";
  return "生成图片";
});

watch(
  () => props.settings.ratio,
  (ratio) => {
    const next = resolveQuality(ratio, props.settings.quality);
    if (next && next !== props.settings.quality) {
      updateSetting("quality", next);
    }
  },
);

function updateSetting(key, value) {
  emit("update:settings", {
    ...props.settings,
    [key]: value,
  });
}

</script>

<template>
  <GeneratorSidePanelShell>
    <ImageUploader
      title="参考图"
      add-text="添加参考图"
      hint-text="可选，最多 9 张"
      alt-text="参考图"
      main-badge-text="参"
      limit-message="最多只能上传 9 张参考图"
      :max-count="9"
      :show-placeholders="false"
      :images="referenceImages"
      :main-index="mainImageIndex"
      @update:images="emit('update:referenceImages', $event)"
      @update:main-index="emit('update:mainImageIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <GeneratorPanelSection title="生成设置">
      <div>
        <div class="mb-1.5 flex items-center justify-between">
          <label class="text-xs font-bold text-slate-800">提示词</label>
          <button
            type="button"
            class="flex cursor-pointer items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-primary shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canOptimize"
            @click="emit('optimize')"
          >
            <LoaderCircle v-if="optimizing" class="h-3.5 w-3.5 animate-spin" />
            <Sparkles v-else class="h-3.5 w-3.5" />
            {{ optimizing ? "AI优化中..." : "AI优化" }}
          </button>
        </div>
        <textarea
          :value="settings.prompt"
          class="h-36 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
          placeholder="输入你想生成的画面，例如：一只透明玻璃杯放在木质餐桌上，柔和自然光，真实摄影风格"
          @input="updateSetting('prompt', $event.target.value)"
        ></textarea>
      </div>

      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-500">图片比例</label>
        <AppSelect
          :model-value="settings.ratio"
          :options="ratioOptions"
          @update:model-value="updateSetting('ratio', $event)"
        />
      </div>

      <ImageQualitySelector
        :model-value="settings.quality"
        :ratio="settings.ratio"
        :output-label="selectedImageLabel"
        @update:model-value="updateSetting('quality', $event)"
      />
    </GeneratorPanelSection>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="primaryText"
        :primary-disabled="!canGenerate"
        @primary="emit('generate')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="creatingBatch" class="h-4 w-4 animate-spin" />
          <ImagePlus v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
