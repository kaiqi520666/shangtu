<script setup>
import { computed, toRefs } from "vue";
import { Languages, Sparkles } from "lucide-vue-next";
import VideoUploader from "@/components/generation/video/VideoUploader.vue";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import AppOptionCards from "@/components/ui/AppOptionCards.vue";
import AppSelect from "@/components/ui/AppSelect.vue";

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  selectedVideo: {
    type: Object,
    default: null,
  },
  languageOptions: {
    type: Array,
    default: () => [],
  },
  qualityOptions: {
    type: Array,
    default: () => [],
  },
  feeText: {
    type: String,
    default: "",
  },
  generateDisabled: {
    type: Boolean,
    default: false,
  },
  generateText: {
    type: String,
    default: "开始翻译",
  },
});

const emit = defineEmits([
  "update:settings",
  "update:selectedVideo",
  "generate",
  "notify",
]);

const { settings, selectedVideo } = toRefs(props);
const durationText = computed(() => {
  const duration = Number(selectedVideo.value?.durationSeconds || 0);
  return duration > 0 ? `已识别视频时长：${duration} 秒` : "上传或选择视频后自动识别时长";
});

function updateSettings(patch) {
  emit("update:settings", {
    ...settings.value,
    ...patch,
  });
}
</script>

<template>
  <GeneratorSidePanelShell>
    <section class="space-y-4 border-b border-slate-100 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">视频翻译</h2>
        <p class="mt-1 text-xs leading-relaxed text-slate-400">上传视频或从资产库选择视频，系统自动识别源语言。</p>
      </div>

      <VideoUploader
        :video="selectedVideo"
        title="视频素材"
        add-text="添加视频"
        hint-text="支持本地上传或资产库选择"
        @update:video="emit('update:selectedVideo', $event)"
        @notify="emit('notify', $event)"
      />
      <p class="text-xs text-slate-400">{{ durationText }}</p>
    </section>

    <section class="space-y-4 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">翻译设置</h2>
      </div>

      <div>
        <div class="mb-2 flex items-center justify-between">
          <h3 class="text-xs font-bold text-slate-800">目标语言</h3>
          <span class="text-[11px] text-slate-400">单选</span>
        </div>
        <AppSelect
          :model-value="settings.targetLanguageId"
          :options="languageOptions"
          placeholder="请选择目标语言"
          @update:model-value="updateSettings({ targetLanguageId: $event })"
        />
      </div>

      <div>
        <div class="mb-2 flex items-center justify-between">
          <h3 class="text-xs font-bold text-slate-800">翻译档位</h3>
          <span class="text-[11px] text-slate-400">均包含唇形同步</span>
        </div>
        <AppOptionCards
          :model-value="settings.qualityTier"
          :options="qualityOptions"
          @update:model-value="updateSettings({ qualityTier: $event })"
        />
      </div>

      <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
        <div class="flex items-start gap-2">
          <Languages class="mt-0.5 h-4 w-4 text-primary" />
          <div>
            <p class="text-xs font-bold text-slate-800">预计扣费</p>
            <p class="mt-1 text-xs leading-relaxed text-slate-500">{{ feeText || "选择视频和档位后显示预计扣费" }}</p>
          </div>
        </div>
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
