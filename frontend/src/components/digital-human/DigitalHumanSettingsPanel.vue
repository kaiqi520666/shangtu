<script setup>
import { Bot, Mic2, Sparkles } from "lucide-vue-next";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import AppSelect from "@/components/ui/AppSelect.vue";

const qualityOptions = [
  { value: "standard", label: "标准档", description: "Avatar III" },
  { value: "premium", label: "高质档", description: "Avatar IV" },
];

defineProps({
  settings: {
    type: Object,
    required: true,
  },
  selectedAvatar: {
    type: Object,
    default: null,
  },
  selectedVoice: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits([
  "update:settings",
  "open-avatar-picker",
  "open-voice-picker",
  "notify",
]);
</script>

<template>
  <GeneratorSidePanelShell>
    <section class="space-y-4 border-b border-slate-100 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">数字人</h2>
        <p class="mt-1 text-xs leading-relaxed text-slate-400">先选系统数字人和系统声音，后续这里会直接接入 HeyGen 出片。</p>
      </div>

      <button
        type="button"
        class="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition-colors hover:border-primary/30 hover:bg-white"
        @click="emit('open-avatar-picker')"
      >
        <span class="flex min-w-0 items-center gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Bot class="h-4.5 w-4.5" />
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

      <button
        type="button"
        class="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition-colors hover:border-primary/30 hover:bg-white"
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
          </span>
        </span>
        <span class="text-xs font-medium text-primary">更换</span>
      </button>
    </section>

    <section class="space-y-4 border-b border-slate-100 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">口播内容</h2>
        <p class="mt-1 text-xs text-slate-400">`口播文案` 用于脚本内容，`动作提示` 用于 motion prompt。</p>
      </div>

      <label class="block">
        <span class="mb-1.5 block text-xs font-bold text-slate-800">口播文案</span>
        <textarea
          :value="settings.script"
          class="h-36 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
          placeholder="输入数字人要说的口播文案..."
          @input="emit('update:settings', { ...settings, script: $event.target.value })"
        ></textarea>
      </label>

      <label class="block">
        <span class="mb-1.5 block text-xs font-bold text-slate-800">动作提示（可选）</span>
        <textarea
          :value="settings.motionPrompt"
          class="h-24 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
          placeholder="例如：自然挥手开场，手势克制，保持专业讲解状态..."
          @input="emit('update:settings', { ...settings, motionPrompt: $event.target.value })"
        ></textarea>
      </label>
    </section>

    <section class="space-y-4 p-5">
      <div>
        <h2 class="text-sm font-black text-slate-900">视频设置</h2>
        <p class="mt-1 text-xs text-slate-400">这里先确定生成档位和比例，后续继续接入字幕、背景和积分规则。</p>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <AppSelect
          :model-value="settings.qualityTier"
          :options="qualityOptions"
          @update:model-value="emit('update:settings', { ...settings, qualityTier: $event })"
        />
        <AppSelect
          :model-value="settings.aspectRatio"
          :options="[
            { value: '9:16', label: '9:16', description: '竖版口播' },
            { value: '16:9', label: '16:9', description: '横版口播' },
            { value: '1:1', label: '1:1', description: '方版口播' },
          ]"
          @update:model-value="emit('update:settings', { ...settings, aspectRatio: $event })"
        />
      </div>
    </section>

    <template #footer>
      <GeneratorActionFooter
        primary-text="下一步接入数字人选择弹窗"
        :primary-disabled="false"
        secondary-text="保存草稿"
        @primary="emit('notify', '数字人和声音选择弹窗将在下一步接入')"
        @secondary="emit('notify', '草稿保存会在后续版本开放')"
      >
        <template #primary-icon>
          <Sparkles class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
