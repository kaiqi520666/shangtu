<script setup>
import { computed, watch } from "vue";
import { ImagePlus, LoaderCircle, Sparkles } from "lucide-vue-next";
import AppSelect from "@/components/ui/AppSelect.vue";
import GeneratorActionFooter from "@/components/generation/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/GeneratorSidePanelShell.vue";
import ImageUploader from "@/components/generation/ImageUploader.vue";
import {
  isQualitySupported,
  qualityOptions,
  ratioOptions,
  resolveQuality,
} from "@/constants/generator.js";

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
  generating: {
    type: Boolean,
    default: false,
  },
  generatedCount: {
    type: Number,
    default: 0,
  },
  totalCount: {
    type: Number,
    default: 1,
  },
  jobTotal: {
    type: Number,
    default: 0,
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

const isQualityEnabled = (quality) => isQualitySupported(props.settings.ratio, quality);

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

function selectQuality(quality) {
  if (!isQualityEnabled(quality)) return;
  updateSetting("quality", quality);
}
</script>

<template>
  <GeneratorSidePanelShell>
    <ImageUploader
      title="参考图"
      add-text="添加参考图"
      hint-text="可选"
      alt-text="参考图"
      main-badge-text="参"
      limit-message="最多只能上传 3 张参考图"
      :images="referenceImages"
      :main-index="mainImageIndex"
      @update:images="emit('update:referenceImages', $event)"
      @update:main-index="emit('update:mainImageIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <section class="space-y-4 border-b border-slate-100 p-5">
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

      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-500">图片质量</label>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="quality in qualityOptions"
            :key="quality.value"
            type="button"
            :disabled="!isQualityEnabled(quality.value)"
            class="rounded-lg border px-3 py-2 text-center transition-all"
            :class="
              !isQualityEnabled(quality.value)
                ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-300'
                : settings.quality === quality.value
                  ? 'border-primary bg-primary/10 text-primary shadow-sm'
                  : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50'
            "
            @click="selectQuality(quality.value)"
          >
            <span class="block text-sm font-bold leading-tight">{{ quality.title }}</span>
            <span
              class="mt-0.5 block text-xs leading-tight"
              :class="
                !isQualityEnabled(quality.value)
                  ? 'text-slate-300'
                  : settings.quality === quality.value
                    ? 'text-primary'
                    : 'text-slate-400'
              "
            >
              {{ isQualityEnabled(quality.value) ? quality.subtitle : "不支持" }}
            </span>
          </button>
        </div>
        <p class="mt-2 text-xs text-slate-400">当前输出：{{ selectedImageLabel }}</p>
      </div>
    </section>

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
