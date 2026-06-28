<script setup>
import { computed } from "vue";
import { Clapperboard, LoaderCircle, Sparkles } from "lucide-vue-next";
import AppSelect from "@/components/ui/AppSelect.vue";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import ImageUploader from "@/components/generation/image/ImageUploader.vue";
import VideoDurationSlider from "@/components/product-video/VideoDurationSlider.vue";
import VideoQualitySelector from "@/components/product-video/VideoQualitySelector.vue";
import {
  freeVideoInputModes,
  freeVideoRatioOptions,
  getFreeVideoInputMode,
} from "@/constants/free-video.js";

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
    default: 0,
  },
  creditCosts: {
    type: Object,
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
  selectedVideoLabel: {
    type: String,
    required: true,
  },
});

const emit = defineEmits([
  "update:settings",
  "update:uploadedImages",
  "update:mainImageIndex",
  "notify",
  "optimize",
  "generate",
]);

const selectedMode = computed(() => getFreeVideoInputMode(props.settings.inputMode));
const showUploader = computed(() => props.settings.inputMode !== "text_to_video");
const maxUploadCount = computed(() => (props.settings.inputMode === "reference_to_video" ? 9 : 1));
const uploadLimitMessage = computed(() =>
  props.settings.inputMode === "reference_to_video"
    ? "参考图最多只能上传 9 张"
    : "图生视频只能上传 1 张首帧图",
);
const primaryText = computed(() => {
  if (!props.settings.prompt.trim()) return "请输入视频提示词";
  if (props.uploadedImages.some((img) => img?.uploading)) return "素材上传中...";
  if (props.creatingBatch) return "正在创建任务...";
  if (props.hasRunningTasks) return "追加生成";
  return "生成视频";
});

function updateSetting(key, value) {
  emit("update:settings", {
    ...props.settings,
    [key]: value,
  });
}

function updateInputMode(mode) {
  emit("update:settings", {
    ...props.settings,
    inputMode: mode,
  });
  emit("update:uploadedImages", []);
  emit("update:mainImageIndex", 0);
}
</script>

<template>
  <GeneratorSidePanelShell>
    <section class="space-y-4 border-b border-slate-100 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">生成模式</h2>
        <div class="mt-3 grid grid-cols-1 gap-2">
          <button
            v-for="mode in freeVideoInputModes"
            :key="mode.value"
            type="button"
            class="rounded-xl border px-3 py-2 text-left transition-all"
            :class="
              settings.inputMode === mode.value
                ? 'border-primary bg-primary/10 text-primary shadow-sm'
                : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50'
            "
            @click="updateInputMode(mode.value)"
          >
            <span class="block text-xs font-black">{{ mode.label }}</span>
            <span
              class="mt-1 block text-xs leading-relaxed"
              :class="settings.inputMode === mode.value ? 'text-primary/80' : 'text-slate-400'"
            >
              {{ mode.description }}
            </span>
          </button>
        </div>
      </div>
    </section>

    <ImageUploader
      v-if="showUploader"
      :images="uploadedImages"
      :main-index="mainImageIndex"
      :title="selectedMode.uploadTitle"
      :max-count="maxUploadCount"
      :add-text="selectedMode.addText"
      :hint-text="selectedMode.hintText"
      alt-text="自由生视频素材"
      main-badge-text="素材"
      :limit-message="uploadLimitMessage"
      :show-placeholders="false"
      @update:images="emit('update:uploadedImages', $event)"
      @update:main-index="emit('update:mainImageIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <section class="space-y-4 border-b border-slate-100 p-5">
      <div>
        <div class="mb-1.5 flex items-center justify-between gap-3">
          <label class="text-xs font-bold text-slate-800">视频提示词</label>
          <button
            v-if="settings.inputMode === 'text_to_video'"
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
          class="h-40 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
          placeholder="描述你想生成的视频内容、动作、镜头和氛围。例如：咖啡杯在晨光中的木桌上轻轻旋转，镜头缓慢推近，水汽升起，真实摄影风格。"
          @input="updateSetting('prompt', $event.target.value)"
        ></textarea>
      </div>

      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-500">视频比例</label>
        <AppSelect
          :model-value="settings.aspectRatio"
          :options="freeVideoRatioOptions"
          @update:model-value="updateSetting('aspectRatio', $event)"
        />
      </div>

      <VideoDurationSlider
        :duration="settings.duration"
        :resolution="settings.resolution"
        :credit-costs="creditCosts"
        @update:duration="updateSetting('duration', $event)"
      />

      <VideoQualitySelector
        :model-value="settings.resolution"
        @update:model-value="updateSetting('resolution', $event)"
      />

      <p class="rounded-lg bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-500">
        当前输出：{{ selectedVideoLabel }}
      </p>
    </section>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="primaryText"
        :primary-disabled="!canGenerate"
        @primary="emit('generate')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="creatingBatch" class="h-4 w-4 animate-spin" />
          <Clapperboard v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
