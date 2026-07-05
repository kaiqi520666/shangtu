<script setup>
import { reactive, ref } from "vue";
import { Bot, Mic2, Sparkles, Video } from "lucide-vue-next";
import AvatarPickerModal from "@/components/digital-human/AvatarPickerModal.vue";
import DigitalHumanSettingsPanel from "@/components/digital-human/DigitalHumanSettingsPanel.vue";
import VoicePickerModal from "@/components/digital-human/VoicePickerModal.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import { useToast } from "@/composables/useToast.js";

const toast = useToast();
const settings = reactive({
  script: "",
  motionPrompt: "",
  qualityTier: "standard",
  resolution: "1080p",
  aspectRatio: "9:16",
  voiceSpeed: 1,
});

const selectedAvatar = ref(null);
const selectedVoice = ref(null);
const avatarPickerOpen = ref(false);
const voicePickerOpen = ref(false);

function showNotice(message) {
  toast.info(message);
}

function openAvatarPicker() {
  avatarPickerOpen.value = true;
}

function openVoicePicker() {
  voicePickerOpen.value = true;
}

function handleAvatarConfirm(item) {
  selectedAvatar.value = item;
}

function handleVoiceConfirm(item) {
  selectedVoice.value = item;
}
</script>

<template>
  <GeneratorLayout>
    <DigitalHumanSettingsPanel
      :settings="settings"
      :selected-avatar="selectedAvatar"
      :selected-voice="selectedVoice"
      @update:settings="Object.assign(settings, $event)"
      @open-avatar-picker="openAvatarPicker"
      @open-voice-picker="openVoicePicker"
      @notify="showNotice"
    />

    <section class="flex min-h-0 flex-1 flex-col overflow-hidden bg-slate-50">
      <div class="border-b border-slate-200 bg-white px-6 py-4">
        <h1 class="text-base font-black text-slate-900">数字人</h1>
        <p class="mt-1 text-xs text-slate-400">先完成正式入口，下一步直接接系统数字人 / 系统声音选择弹窗和 HeyGen 任务链路。</p>
      </div>

      <div class="flex-1 overflow-y-auto p-6">
        <div class="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex items-center gap-2 text-slate-800">
              <Video class="h-4.5 w-4.5 text-primary" />
              <h2 class="text-sm font-black">生成工作区</h2>
            </div>
            <div class="mt-4 flex min-h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 text-center">
              <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <Bot class="h-6 w-6" />
              </div>
              <p class="mt-4 text-sm font-bold text-slate-800">数字人功能入口已就位</p>
              <p class="mt-2 max-w-md text-xs leading-relaxed text-slate-400">
                下一步会把系统数字人选择、系统声音选择、HeyGen 任务创建和结果轮询依次接进这里。
              </p>
            </div>
          </section>

          <section class="space-y-4">
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center gap-2 text-slate-800">
                <Bot class="h-4.5 w-4.5 text-primary" />
                <h2 class="text-sm font-black">当前数字人</h2>
              </div>
              <div v-if="selectedAvatar?.preview_image_url" class="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
                <img :src="selectedAvatar.preview_image_url" class="h-36 w-full object-cover" alt="当前数字人预览" />
              </div>
              <p class="mt-3 text-xs font-medium text-slate-700">{{ selectedAvatar?.name || "暂未选择系统数字人" }}</p>
              <p class="mt-1 text-xs text-slate-400">{{ selectedAvatar?.avatar_id || "选择后会在这里显示 avatar_id" }}</p>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center gap-2 text-slate-800">
                <Mic2 class="h-4.5 w-4.5 text-secondary" />
                <h2 class="text-sm font-black">当前声音</h2>
              </div>
              <p class="mt-3 text-xs font-medium text-slate-700">{{ selectedVoice?.name || "暂未选择系统声音" }}</p>
              <p class="mt-1 text-xs text-slate-400">{{ selectedVoice?.language || "选择后会在这里显示语言" }}</p>
              <div v-if="selectedVoice?.preview_audio_url" class="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
                <audio :src="selectedVoice.preview_audio_url" controls preload="none" class="h-10 w-full"></audio>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div class="flex items-center gap-2 text-slate-800">
                <Sparkles class="h-4.5 w-4.5 text-primary" />
                <h2 class="text-sm font-black">当前设置</h2>
              </div>
              <dl class="mt-3 space-y-2 text-xs text-slate-500">
                <div class="flex items-center justify-between gap-3">
                  <dt>生成档位</dt>
                  <dd class="font-medium text-slate-700">{{ settings.qualityTier === "premium" ? "高质档" : "标准档" }}</dd>
                </div>
                <div class="flex items-center justify-between gap-3">
                  <dt>画面比例</dt>
                  <dd class="font-medium text-slate-700">{{ settings.aspectRatio }}</dd>
                </div>
                <div class="flex items-center justify-between gap-3">
                  <dt>视频清晰度</dt>
                  <dd class="font-medium text-slate-700">{{ settings.resolution }}</dd>
                </div>
                <div class="flex items-center justify-between gap-3">
                  <dt>语速</dt>
                  <dd class="font-medium text-slate-700">{{ settings.voiceSpeed }}x</dd>
                </div>
                <div class="flex items-center justify-between gap-3">
                  <dt>口播文案</dt>
                  <dd class="font-medium text-slate-700">{{ settings.script ? "已填写" : "未填写" }}</dd>
                </div>
              </dl>
            </div>
          </section>
        </div>
      </div>
    </section>

    <AvatarPickerModal
      :open="avatarPickerOpen"
      :selected-avatar="selectedAvatar"
      @close="avatarPickerOpen = false"
      @confirm="handleAvatarConfirm"
      @notify="showNotice"
    />

    <VoicePickerModal
      :open="voicePickerOpen"
      :selected-voice="selectedVoice"
      @close="voicePickerOpen = false"
      @confirm="handleVoiceConfirm"
      @notify="showNotice"
    />
  </GeneratorLayout>
</template>
