<script setup>
import { computed } from "vue";
import { Sparkles, WandSparkles } from "lucide-vue-next";
import GeneratorActionFooter from "@/components/generation/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/GeneratorSidePanelShell.vue";
import ImageUploader from "@/components/generation/ImageUploader.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import VideoDurationSlider from "@/components/product-video/VideoDurationSlider.vue";
import VideoQualitySelector from "@/components/product-video/VideoQualitySelector.vue";
import VideoTypeSelector from "@/components/product-video/VideoTypeSelector.vue";
import {
  defaultVideoCreditCosts,
  getVideoCreditCost,
  getVideoDemoType,
  videoLanguageOptions,
  videoMarketOptions,
  videoSizeOptions,
} from "@/constants/productVideo.js";

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
    default: () => defaultVideoCreditCosts,
  },
});

const emit = defineEmits([
  "update:settings",
  "update:uploadedImages",
  "update:mainImageIndex",
  "notify",
  "generate",
]);

const selectedType = computed(() => getVideoDemoType(props.settings.videoType));
const maxUploadCount = computed(() => {
  if (selectedType.value.inputMode === "reference_images") return 9;
  if (selectedType.value.inputMode === "first_last_frame") return 2;
  return 1;
});
const uploadAddText = computed(() => {
  if (selectedType.value.inputMode === "first_last_frame") {
    return props.uploadedImages.length === 0 ? "添加开始图" : "添加结束图";
  }
  return "添加素材";
});
const uploadRoleText = computed(() => {
  if (selectedType.value.inputMode === "first_frame") return "当前将作为视频开头画面生成";
  if (selectedType.value.inputMode === "first_last_frame") return "当前将生成从开始图到结束图的变化视频";
  return "当前将参考多张图片生成视频";
});
const estimatedCredits = computed(() =>
  getVideoCreditCost({
    resolution: props.settings.resolution,
    duration: props.settings.duration,
    costs: props.creditCosts,
  }),
);
const generateDisabled = computed(() => {
  if (props.uploadedImages.some((img) => img?.uploading)) return true;
  if (selectedType.value.inputMode === "first_last_frame") return props.uploadedImages.length < 2;
  return props.uploadedImages.length < 1;
});
const generateText = computed(() => {
  if (props.uploadedImages.some((img) => img?.uploading)) return "素材上传中...";
  if (generateDisabled.value) return selectedType.value.inputMode === "first_last_frame" ? "请上传开始图和结束图" : "请先上传素材";
  return `生成视频 · ${estimatedCredits.value || "-"} 积分`;
});

function updateSetting(key, value) {
  emit("update:settings", {
    ...props.settings,
    [key]: value,
  });
}

function updateVideoType(typeId) {
  const nextType = getVideoDemoType(typeId);
  emit("update:settings", {
    ...props.settings,
    videoType: typeId,
    inputMode: nextType.inputMode,
  });
  emit("update:uploadedImages", []);
  emit("update:mainImageIndex", 0);
}

function notifyPending(featureName) {
  emit("notify", `${featureName}会在商品视频后端接入时开放`);
}
</script>

<template>
  <GeneratorSidePanelShell>
    <VideoTypeSelector :model-value="settings.videoType" @update:model-value="updateVideoType" />

    <ImageUploader
      :images="uploadedImages"
      :main-index="mainImageIndex"
      :title="selectedType.uploadTitle"
      :max-count="maxUploadCount"
      :add-text="uploadAddText"
      :hint-text="selectedType.uploadHint"
      alt-text="商品视频素材"
      main-badge-text="素材"
      :limit-message="`最多只能上传 ${maxUploadCount} 张素材`"
      @update:images="emit('update:uploadedImages', $event)"
      @update:main-index="emit('update:mainImageIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <section class="space-y-4 border-b border-slate-100 p-5">
      <div class="rounded-xl border border-primary/15 bg-primary/5 px-3 py-2 text-xs font-semibold text-primary">
        {{ uploadRoleText }}
      </div>

      <div>
        <h2 class="text-sm font-black text-slate-900">目标市场与语言</h2>
        <div class="mt-3 grid grid-cols-2 gap-3">
          <AppSelect :model-value="settings.market" :options="videoMarketOptions" @update:model-value="updateSetting('market', $event)" />
          <AppSelect :model-value="settings.language" :options="videoLanguageOptions" @update:model-value="updateSetting('language', $event)" />
        </div>
        <div class="mt-3">
          <AppSelect :model-value="settings.sizePreset" :options="videoSizeOptions" @update:model-value="updateSetting('sizePreset', $event)" />
        </div>
      </div>

      <VideoDurationSlider
        :duration="settings.duration"
        :resolution="settings.resolution"
        :credit-costs="creditCosts"
        @update:duration="updateSetting('duration', $event)"
      />

      <VideoQualitySelector :model-value="settings.resolution" @update:model-value="updateSetting('resolution', $event)" />

      <div>
        <div class="mb-1.5 flex items-center justify-between">
          <label class="text-xs font-bold text-slate-800">商品卖点 / 视频要求</label>
          <button
            type="button"
            class="flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-primary shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5"
            @click="notifyPending('AI 帮写')"
          >
            <Sparkles class="h-3.5 w-3.5" />
            AI 帮写
          </button>
        </div>
        <textarea
          :value="settings.productInput"
          class="h-32 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
          placeholder="输入商品核心卖点、适用人群、使用场景、希望呈现的视频氛围..."
          @input="updateSetting('productInput', $event.target.value)"
        ></textarea>
      </div>
    </section>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="generateText"
        :primary-disabled="generateDisabled"
        secondary-text="保存草稿"
        @primary="emit('generate')"
        @secondary="notifyPending('草稿保存')"
      >
        <template #primary-icon>
          <WandSparkles class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
