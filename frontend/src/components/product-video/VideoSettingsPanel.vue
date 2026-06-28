<script setup>
import { computed } from "vue";
import { WandSparkles } from "lucide-vue-next";
import GeneratorActionFooter from "@/components/generation/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/GeneratorSidePanelShell.vue";
import ImageUploader from "@/components/generation/image/ImageUploader.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import VideoDurationSlider from "@/components/product-video/VideoDurationSlider.vue";
import VideoQualitySelector from "@/components/product-video/VideoQualitySelector.vue";
import VideoTypeSelector from "@/components/product-video/VideoTypeSelector.vue";
import {
  defaultVideoCreditCosts,
  getVideoDemoType,
  videoLanguageOptions,
  videoMarketOptions,
  videoSizeOptions,
} from "@/constants/product-video.js";

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
  canGenerateStrategy: {
    type: Boolean,
    default: false,
  },
  strategyLoading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  "update:settings",
  "update:uploadedImages",
  "update:mainImageIndex",
  "notify",
  "generate-strategy",
]);

const selectedType = computed(() => getVideoDemoType(props.settings.videoType));
const maxUploadCount = computed(() => {
  if (selectedType.value.inputMode === "reference_to_video") return 9;
  return 1;
});
const uploadAddText = computed(() => {
  if (selectedType.value.inputMode === "reference_to_video") return "添加参考图";
  return "添加首帧图";
});
const uploadHintText = computed(() => {
  if (selectedType.value.inputMode === "reference_to_video") return "支持 1-9 张";
  return "必须上传 1 张";
});
const uploadRoleText = computed(() => {
  if (selectedType.value.inputMode === "image_to_video") return "当前将作为视频开头画面生成";
  return "当前将参考多张图片生成视频";
});
const uploadRequirementText = computed(() => {
  if (selectedType.value.inputMode === "image_to_video") {
    return "上传 1 张商品或人物首帧图，系统会从这张画面开始生成视频。";
  }
  return "至少上传 1 张产品参考图，最多 9 张；图片越完整，产品还原越稳定。";
});
const uploadLimitMessage = computed(() => {
  if (selectedType.value.inputMode === "reference_to_video") return "参考图最多只能上传 9 张";
  return "图生视频只能上传 1 张图片";
});
const showUploadPlaceholders = computed(() => false);
const showMainImageAction = computed(() => false);
const badgeTextResolver = computed(() => null);
const generateDisabled = computed(() => {
  if (props.strategyLoading) return true;
  if (props.uploadedImages.some((img) => img?.uploading)) return true;
  return props.uploadedImages.length < 1;
});
const generateText = computed(() => {
  if (props.strategyLoading) return "AI 正在生成提示词...";
  if (props.uploadedImages.some((img) => img?.uploading)) return "素材上传中...";
  if (generateDisabled.value) {
    if (selectedType.value.inputMode === "reference_to_video") return "请至少上传 1 张参考图";
    return "请上传 1 张首帧图";
  }
  return "AI 生成视频提示词";
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
  emit("notify", `${featureName}会在后续版本开放`);
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
      :hint-text="uploadHintText"
      alt-text="商品视频素材"
      main-badge-text="素材"
      :limit-message="uploadLimitMessage"
      :show-placeholders="showUploadPlaceholders"
      :show-main-action="showMainImageAction"
      :badge-text-resolver="badgeTextResolver"
      @update:images="emit('update:uploadedImages', $event)"
      @update:main-index="emit('update:mainImageIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <section class="space-y-4 border-b border-slate-100 p-5">
      <div class="space-y-1.5 rounded-xl border border-primary/15 bg-primary/5 px-3 py-2 text-xs font-semibold text-primary">
        <p>{{ uploadRoleText }}</p>
        <p class="font-medium leading-relaxed text-primary/80">{{ uploadRequirementText }}</p>
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
        <label class="mb-1.5 block text-xs font-bold text-slate-800">补充要求（可选）</label>
        <textarea
          :value="settings.productInput"
          class="h-32 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
          placeholder="可补充商品卖点、适用人群、使用场景或希望呈现的视频氛围..."
          @input="updateSetting('productInput', $event.target.value)"
        ></textarea>
      </div>
    </section>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="generateText"
        :primary-disabled="!canGenerateStrategy || generateDisabled"
        secondary-text="保存草稿"
        @primary="emit('generate-strategy')"
        @secondary="notifyPending('草稿保存')"
      >
        <template #primary-icon>
          <WandSparkles class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
