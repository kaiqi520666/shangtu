<script setup>
import { computed, ref } from "vue";
import { AudioLines, ChevronRight, Mic2 } from "lucide-vue-next";
import VoicePickerModal from "@/components/voiceover/VoicePickerModal.vue";

const props = defineProps({ settings: { type: Object, required: true }, config: { type: Object, required: true }, canGenerate: { type: Boolean, default: false }, creating: { type: Boolean, default: false } });
const emit = defineEmits(["update:settings", "generate", "notify"]);
const pickerOpen = ref(false);
const characterCount = computed(() => String(props.settings.text || "").replace(/\s/g, "").length);
const estimatedCredits = computed(() => Math.ceil(characterCount.value / 100) * Number(props.config.creditCostPer100Chars || 1));

function update(key, value) { emit("update:settings", { [key]: value }); }
</script>

<template>
  <aside class="flex h-full w-[360px] shrink-0 flex-col border-r border-slate-200 bg-white">
    <div class="border-b border-slate-200 px-5 py-4"><div class="flex items-center gap-2"><AudioLines class="h-5 w-5 text-primary" /><h1 class="text-base font-bold text-slate-800">AI 配音</h1></div></div>
    <div class="min-h-0 flex-1 space-y-5 overflow-y-auto p-5">
      <section><label class="text-xs font-bold text-slate-600">音色</label><button type="button" class="mt-2 flex w-full items-center gap-3 border border-slate-200 bg-slate-50 p-3 text-left hover:border-primary/40" @click="pickerOpen = true"><span class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary"><Mic2 class="h-4 w-4" /></span><span class="min-w-0 flex-1"><strong class="block truncate text-sm text-slate-800">{{ settings.voice?.name || '选择音色' }}</strong><span class="block truncate text-xs text-slate-400">{{ settings.voice?.trait || '试听并选择预置音色' }}</span></span><ChevronRight class="h-4 w-4 text-slate-400" /></button></section>
      <section><div class="flex items-center justify-between"><label class="text-xs font-bold text-slate-600">配音文本</label><span class="text-xs" :class="characterCount > config.textLimit ? 'text-rose-500' : 'text-slate-400'">{{ characterCount }} / {{ config.textLimit }}</span></div><textarea :value="settings.text" rows="12" class="mt-2 w-full resize-none border border-slate-200 p-3 text-sm leading-6 outline-none focus:border-primary" placeholder="输入需要转换为语音的文本" @input="update('text', $event.target.value)"></textarea></section>
      <section class="grid grid-cols-1 gap-4">
        <label class="text-xs font-bold text-slate-600">语速 {{ Number(settings.rate).toFixed(1) }}<input :value="settings.rate" type="range" min="0.5" max="2" step="0.1" class="mt-2 w-full accent-primary" @input="update('rate', Number($event.target.value))" /></label>
        <label class="text-xs font-bold text-slate-600">音调 {{ Number(settings.pitch).toFixed(1) }}<input :value="settings.pitch" type="range" min="0.5" max="2" step="0.1" class="mt-2 w-full accent-primary" @input="update('pitch', Number($event.target.value))" /></label>
        <label class="text-xs font-bold text-slate-600">音量 {{ settings.volume }}<input :value="settings.volume" type="range" min="0" max="100" step="1" class="mt-2 w-full accent-primary" @input="update('volume', Number($event.target.value))" /></label>
      </section>
      <section v-if="settings.voice?.supports_instruct"><div class="flex items-center justify-between"><label class="text-xs font-bold text-slate-600">表达指令</label><span class="text-xs text-slate-400">{{ settings.instruction.length }} / 100</span></div><textarea :value="settings.instruction" maxlength="100" rows="3" class="mt-2 w-full resize-none border border-slate-200 p-3 text-sm outline-none focus:border-primary" placeholder="例如：用温柔、舒缓的语气讲述" @input="update('instruction', $event.target.value)"></textarea></section>
    </div>
    <div class="border-t border-slate-200 p-5"><div class="mb-3 flex items-center justify-between text-xs"><span class="text-slate-500">预计消耗</span><strong class="text-primary">{{ estimatedCredits }} 积分</strong></div><button type="button" class="w-full bg-primary px-4 py-3 text-sm font-bold text-white hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50" :disabled="!canGenerate || creating" @click="emit('generate')">{{ creating ? '正在创建...' : '生成配音' }}</button></div>
    <VoicePickerModal :open="pickerOpen" :selected-voice="settings.voice" @close="pickerOpen = false" @confirm="update('voice', $event)" @notify="emit('notify', $event)" />
  </aside>
</template>
