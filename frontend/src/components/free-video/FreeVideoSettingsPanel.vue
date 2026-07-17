<script setup>
import { computed } from "vue";
import { Clapperboard, LoaderCircle, Search, Volume2 } from "lucide-vue-next";
import AppSelect from "@/components/ui/AppSelect.vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorPanelSection from "@/components/generation/workspace/GeneratorPanelSection.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import AiAssistedTextarea from "@/components/generation/workspace/AiAssistedTextarea.vue";
import ImageUploader from "@/components/generation/image/ImageUploader.vue";
import MediaUploader from "@/components/generation/media/MediaUploader.vue";
import VideoDurationSlider from "@/components/product-video/VideoDurationSlider.vue";
import VideoQualitySelector from "@/components/product-video/VideoQualitySelector.vue";
import { freeVideoRatioOptions } from "@/constants/free-video.js";
import { videoResolutionOptions } from "@/constants/product-video.js";

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  uploadedImages: {
    type: Array,
    required: true,
  },
  uploadedVideos: {
    type: Array,
    required: true,
  },
  uploadedAudios: {
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
  optimizePrompt: {
    type: Function,
    required: true,
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
  "update:uploadedVideos",
  "update:uploadedAudios",
  "update:mainImageIndex",
  "notify",
  "generate",
]);

const primaryText = computed(() => {
  if (!props.settings.prompt.trim()) return "请输入视频提示词";
  if (props.uploadedImages.some((img) => img?.uploading)) return "素材上传中...";
  if (props.uploadedVideos.some((item) => item?.uploading)) return "参考视频上传中...";
  if (props.uploadedAudios.some((item) => item?.uploading)) return "参考音频上传中...";
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

</script>

<template>
  <GeneratorSidePanelShell>
    <ImageUploader
      :images="uploadedImages"
      :main-index="mainImageIndex"
      title="参考图片"
      :max-count="9"
      add-text="添加参考图"
      hint-text="可选，最多 9 张"
      alt-text="自由生视频素材"
      main-badge-text="素材"
      limit-message="参考图最多只能上传 9 张"
      :show-placeholders="false"
      :show-main-action="false"
      @update:images="emit('update:uploadedImages', $event)"
      @update:main-index="emit('update:mainImageIndex', $event)"
      @notify="emit('notify', $event)"
    />

    <MediaUploader
      :items="uploadedVideos"
      media-type="video"
      title="参考视频"
      add-text="添加参考视频"
      hint-text="可选，最多 3 条"
      :max-count="3"
      limit-message="参考视频最多只能上传 3 条"
      @update:items="emit('update:uploadedVideos', $event)"
      @notify="emit('notify', $event)"
    />

    <MediaUploader
      :items="uploadedAudios"
      media-type="audio"
      title="参考音频"
      add-text="添加参考音频"
      hint-text="可选，最多 3 条"
      :max-count="3"
      limit-message="参考音频最多只能上传 3 条"
      @update:items="emit('update:uploadedAudios', $event)"
      @notify="emit('notify', $event)"
    />

    <GeneratorPanelSection title="生成设置">
      <AiAssistedTextarea
        :model-value="settings.prompt"
        label="视频提示词"
        action-label="AI 优化"
        loading-label="AI 优化中..."
        :rows="7"
        :generate-draft="optimizePrompt"
        placeholder="描述你想生成的视频内容、动作、镜头和氛围。例如：咖啡杯在晨光中的木桌上轻轻旋转，镜头缓慢推近，水汽升起，真实摄影风格。"
        @update:model-value="updateSetting('prompt', $event)"
      />

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
        :options="videoResolutionOptions"
        @update:model-value="updateSetting('resolution', $event)"
      />

      <div class="grid gap-2">
        <div
          class="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2.5 transition-colors hover:border-primary/30 hover:bg-primary/5"
        >
          <span class="flex items-center gap-2 text-xs font-bold text-slate-700">
            <Volume2 class="h-4 w-4 text-primary" />
            生成音频
          </span>
          <AppCheckbox
            :model-value="settings.generateAudio"
            size="sm"
            @update:model-value="updateSetting('generateAudio', $event)"
          />
        </div>
        <div
          class="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2.5 transition-colors hover:border-primary/30 hover:bg-primary/5"
        >
          <span class="flex items-center gap-2 text-xs font-bold text-slate-700">
            <Search class="h-4 w-4 text-primary" />
            开启联网搜索
          </span>
          <AppCheckbox
            :model-value="settings.enableWebSearch"
            size="sm"
            @update:model-value="updateSetting('enableWebSearch', $event)"
          />
        </div>
      </div>

      <p class="rounded-lg bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-500">
        当前输出：{{ selectedVideoLabel }}
      </p>
    </GeneratorPanelSection>

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
