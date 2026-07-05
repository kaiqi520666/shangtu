<script setup>
import { toRefs } from "vue";
import { Bot, Mic2, Sparkles } from "lucide-vue-next";
import ImageUploader from "@/components/generation/image/ImageUploader.vue";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import VideoQualitySelector from "@/components/product-video/VideoQualitySelector.vue";
import AppOptionCards from "@/components/ui/AppOptionCards.vue";
import AppRangeCard from "@/components/ui/AppRangeCard.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
const aspectRatioOptions = [
  { value: "9:16", label: "9:16", description: "竖版口播" },
  { value: "16:9", label: "16:9", description: "横版口播" },
  { value: "1:1", label: "1:1", description: "方版口播" },
];
const voiceSpeedMin = 0.8;
const voiceSpeedMax = 1.2;
const voiceSpeedStep = 0.1;

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  qualityOptions: {
    type: Array,
    default: () => [],
  },
  selectedAvatar: {
    type: Object,
    default: null,
  },
  selectedVoice: {
    type: Object,
    default: null,
  },
  backgroundImages: {
    type: Array,
    default: () => [],
  },
  generateDisabled: {
    type: Boolean,
    default: false,
  },
  generateText: {
    type: String,
    default: "生成视频",
  },
  scriptMetaText: {
    type: String,
    default: "",
  },
  scriptExceeded: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  "update:settings",
  "open-avatar-picker",
  "open-voice-picker",
  "update:backgroundImages",
  "generate",
  "notify",
]);

const { settings, selectedAvatar, selectedVoice, backgroundImages } = toRefs(props);

function updateSettings(patch) {
  emit("update:settings", {
    ...settings.value,
    ...patch,
  });
}

function updateVoiceSpeed(event) {
  updateSettings({
    voiceSpeed: Number(event),
  });
}

function formatVoiceSpeed(speed) {
  return `${Number(speed || 1).toFixed(1)}x`;
}

function getVoiceSpeedHint(speed) {
  if (speed <= 0.9) return "语速偏慢，适合更稳的讲解节奏";
  if (speed >= 1.1) return "语速更快，适合节奏更利落的口播";
  return "标准语速，适合大多数口播场景";
}
</script>

<template>
  <GeneratorSidePanelShell>
    <section class="space-y-4 border-b border-slate-100 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">数字人</h2>
        <p class="mt-1 text-xs leading-relaxed text-slate-400">先选系统数字人和系统声音，然后生成视频</p>
      </div>

      <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <button
          type="button"
          class="flex w-full items-center justify-between bg-slate-50 px-4 py-3 text-left transition-colors hover:bg-white"
          @click="emit('open-avatar-picker')"
        >
          <span class="flex min-w-0 items-center gap-3">
            <span class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-primary/10 text-primary">
              <img
                v-if="selectedAvatar?.preview_image_url"
                :src="selectedAvatar.preview_image_url"
                class="h-full w-full object-cover"
                alt="数字人缩略图"
              />
              <Bot v-else class="h-4.5 w-4.5" />
            </span>
            <span class="min-w-0">
              <span class="block text-xs font-bold text-slate-800">选择数字人</span>
              <span class="mt-0.5 block truncate text-xs text-slate-400">
                {{ selectedAvatar?.name || "未选择系统数字人" }}
              </span>
            </span>
          </span>
          <span class="text-xs font-medium text-primary">更换</span>
        </button>

        <div v-if="selectedAvatar?.preview_image_url" class="border-t border-slate-100 p-3">
          <img :src="selectedAvatar.preview_image_url" class="h-40 w-full rounded-xl object-cover" alt="已选数字人预览" />
        </div>
      </section>

      <ImageUploader
        :images="backgroundImages"
        :main-index="0"
        title="背景图"
        :max-count="1"
        add-text="添加图片"
        hint-text="拖拽或点击"
        alt-text="数字人背景图"
        main-badge-text="背景"
        limit-message="背景图只能上传 1 张"
        :show-placeholders="false"
        :show-main-action="false"
        @update:images="emit('update:backgroundImages', $event)"
        @notify="emit('notify', $event)"
      />

      <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <button
          type="button"
          class="flex w-full items-center justify-between bg-slate-50 px-4 py-3 text-left transition-colors hover:bg-white"
          @click="emit('open-voice-picker')"
        >
          <span class="flex min-w-0 items-center gap-3">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
              <Mic2 class="h-4.5 w-4.5" />
            </span>
            <span class="min-w-0">
              <span class="block text-xs font-bold text-slate-800">选择声音</span>
              <span class="mt-0.5 block truncate text-xs text-slate-400">
                {{ selectedVoice?.name || "未选择系统声音" }}
              </span>
              <span v-if="selectedVoice?.language" class="mt-1 block truncate text-[11px] text-slate-400">
                {{ selectedVoice.language }}
              </span>
            </span>
          </span>
          <span class="text-xs font-medium text-primary">更换</span>
        </button>

        <div v-if="selectedVoice?.preview_audio_url" class="border-t border-slate-100 p-3">
          <p class="mb-2 text-[11px] font-bold text-slate-500">声音试听</p>
          <audio :src="selectedVoice.preview_audio_url" controls preload="none" class="h-10 w-full"></audio>
        </div>
      </section>
    </section>

    <section class="space-y-4 border-b border-slate-100 p-5">
      <label class="block">
        <span class="mb-1.5 block text-xs font-bold text-slate-800">口播文案</span>
        <textarea
          :value="settings.script"
          class="h-36 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
          :class="scriptExceeded ? 'border-rose-300 focus:border-rose-400 focus:ring-rose-400' : ''"
          placeholder="输入数字人要说的口播文案..."
          @input="updateSettings({ script: $event.target.value })"
        ></textarea>
        <div class="mt-2 flex items-center justify-between text-[11px]">
          <span :class="scriptExceeded ? 'font-semibold text-rose-500' : 'text-slate-400'">
            {{ scriptMetaText || "当前最长支持约 5 分钟口播文案" }}
          </span>
          <span :class="scriptExceeded ? 'font-semibold text-rose-500' : 'text-slate-400'">
            按 5 字/秒估算
          </span>
        </div>
      </label>

    </section>

    <section class="space-y-4 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">视频设置</h2>
      </div>

      <div class="space-y-4">
        <div>
          <div class="mb-2 flex items-center justify-between">
            <h3 class="text-xs font-bold text-slate-800">生成档位</h3>
            <span class="text-[11px] text-slate-400">按预算和质感选择</span>
          </div>
          <AppOptionCards :model-value="settings.qualityTier" :options="qualityOptions" @update:model-value="updateSettings({ qualityTier: $event })" />
        </div>

        <div>
          <div class="mb-2 flex items-center justify-between">
            <h3 class="text-xs font-bold text-slate-800">视频比例</h3>
            <span class="text-[11px] text-slate-400">按投放平台选择</span>
          </div>
          <AppSelect
            :model-value="settings.aspectRatio"
            :options="aspectRatioOptions"
            @update:model-value="updateSettings({ aspectRatio: $event })"
          />
        </div>

        <VideoQualitySelector :model-value="settings.resolution" @update:model-value="updateSettings({ resolution: $event })" />

        <AppRangeCard
          :model-value="settings.voiceSpeed"
          title="语速调节"
          :hint="getVoiceSpeedHint(settings.voiceSpeed)"
          :min="voiceSpeedMin"
          :max="voiceSpeedMax"
          :step="voiceSpeedStep"
          :min-label="formatVoiceSpeed(voiceSpeedMin)"
          :mid-label="formatVoiceSpeed(1)"
          :max-label="formatVoiceSpeed(voiceSpeedMax)"
          :value-formatter="formatVoiceSpeed"
          @update:model-value="updateVoiceSpeed"
        />
      </div>
    </section>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="generateText"
        :primary-disabled="generateDisabled"
        @primary="emit('generate')"
      >
        <template #primary-icon>
          <Sparkles class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
