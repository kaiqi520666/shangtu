<script setup>
import { computed, ref } from "vue";
import { AudioLines, ChevronRight, LoaderCircle, Mic2 } from "lucide-vue-next";
import GeneratorActionFooter from "@/components/generation/workspace/GeneratorActionFooter.vue";
import GeneratorPanelSection from "@/components/generation/workspace/GeneratorPanelSection.vue";
import GeneratorSidePanelShell from "@/components/generation/workspace/GeneratorSidePanelShell.vue";
import AppRangeCard from "@/components/ui/AppRangeCard.vue";
import VoicePickerModal from "@/components/voiceover/VoicePickerModal.vue";

const props = defineProps({ settings: { type: Object, required: true }, config: { type: Object, required: true }, canGenerate: { type: Boolean, default: false }, creating: { type: Boolean, default: false } });
const emit = defineEmits(["update:settings", "generate", "notify"]);
const pickerOpen = ref(false);
const characterCount = computed(() => String(props.settings.text || "").replace(/\s/g, "").length);
const primaryText = computed(() => props.creating ? "正在创建..." : "生成配音");

function update(key, value) { emit("update:settings", { [key]: value }); }
</script>

<template>
  <GeneratorSidePanelShell>
    <GeneratorPanelSection title="音色">
      <button type="button" class="flex w-full items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-left hover:border-primary/40" @click="pickerOpen = true"><span class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary"><Mic2 class="h-4 w-4" /></span><span class="min-w-0 flex-1"><strong class="block truncate text-sm text-slate-800">{{ settings.voice?.name || '选择音色' }}</strong><span class="block truncate text-xs text-slate-400">{{ settings.voice?.trait || '试听并选择预置音色' }}</span></span><ChevronRight class="h-4 w-4 text-slate-400" /></button>
    </GeneratorPanelSection>
    <GeneratorPanelSection title="配音文本">
      <template #meta>
        <span class="text-xs font-normal" :class="characterCount > config.textLimit ? 'text-rose-500' : 'text-slate-400'">{{ characterCount }} / {{ config.textLimit }}</span>
      </template>
      <textarea :value="settings.text" rows="12" class="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm leading-6 outline-none focus:border-primary" placeholder="输入需要转换为语音的文本" @input="update('text', $event.target.value)"></textarea>
    </GeneratorPanelSection>
    <GeneratorPanelSection title="声音参数" :divider="Boolean(settings.voice?.supports_instruct)">
      <div class="space-y-3">
        <AppRangeCard :model-value="settings.rate" title="语速" :min="0.5" :max="2" :step="0.1" min-label="慢" max-label="快" :value-formatter="(value) => Number(value).toFixed(1)" @update:model-value="update('rate', $event)" />
        <AppRangeCard :model-value="settings.pitch" title="音调" :min="0.5" :max="2" :step="0.1" min-label="低" max-label="高" :value-formatter="(value) => Number(value).toFixed(1)" @update:model-value="update('pitch', $event)" />
        <AppRangeCard :model-value="settings.volume" title="音量" :min="0" :max="100" min-label="静音" max-label="最大" @update:model-value="update('volume', $event)" />
      </div>
    </GeneratorPanelSection>
    <GeneratorPanelSection v-if="settings.voice?.supports_instruct" title="表达指令" :divider="false">
      <template #meta><span class="text-xs font-normal text-slate-400">{{ settings.instruction.length }} / 100</span></template>
      <textarea :value="settings.instruction" maxlength="100" rows="3" class="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm outline-none focus:border-primary" placeholder="例如：用温柔、舒缓的语气讲述" @input="update('instruction', $event.target.value)"></textarea>
    </GeneratorPanelSection>
    <template #footer>
      <GeneratorActionFooter :primary-text="primaryText" :primary-disabled="!canGenerate || creating" @primary="emit('generate')">
        <template #primary-icon><LoaderCircle v-if="creating" class="h-4 w-4 animate-spin" /><AudioLines v-else class="h-4 w-4" /></template>
      </GeneratorActionFooter>
    </template>
    <VoicePickerModal :open="pickerOpen" :selected-voice="settings.voice" @close="pickerOpen = false" @confirm="update('voice', $event)" @notify="emit('notify', $event)" />
  </GeneratorSidePanelShell>
</template>
