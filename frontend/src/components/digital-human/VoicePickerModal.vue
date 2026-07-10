<script setup>
import { computed, ref, watch } from "vue";
import { Mic2 } from "lucide-vue-next";
import { getDigitalHumanVoices } from "@/api/digitalHuman.js";
import HeygenPickerModalShell from "@/components/digital-human/HeygenPickerModalShell.vue";
import UploadedAudioPanel from "@/components/digital-human/UploadedAudioPanel.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { normalizeUploadAudio, useAudioAssets } from "@/composables/digital-human/useAudioAssets.js";
import { useHeygenResourcePicker } from "@/composables/digital-human/useHeygenResourcePicker.js";
import { heygenGenderOptions, heygenVoiceLanguageOptions, heygenVoiceLocaleOptions } from "@/constants/admin.js";

const props = defineProps({ open: { type: Boolean, default: false }, selectedVoice: { type: Object, default: null } });
const emit = defineEmits(["close", "confirm", "notify"]);
const tabs = [{ value: "platform", label: "平台声音" }, { value: "upload", label: "上传音频" }];
const activeTab = ref("platform");
const pendingVoice = ref(null);
const platformPicker = useHeygenResourcePicker({
  listApi: getDigitalHumanVoices,
  defaultFilters: { language: "", gender: "", support_locale: "" },
  buildParams: ({ page, pageSize, keyword, filters }) => ({ page, page_size: pageSize, keyword: keyword || undefined, language: filters.language || undefined, gender: filters.gender || undefined, support_locale: filters.support_locale || undefined }),
});
const audio = useAudioAssets({ selectedVoice: pendingVoice, notify: (message) => emit("notify", message) });
const summary = computed(() => activeTab.value === "platform" ? `共 ${platformPicker.state.total} 个平台声音` : "");

function normalizePlatformVoice(item) {
  return item?.voice_id ? { ...item, mode: "platform" } : null;
}
function normalizeSelectedVoice(item) {
  if (!item) return null;
  return item.mode === "upload" || item.audio_asset_id || item.audio_url ? normalizeUploadAudio(item) : normalizePlatformVoice(item);
}

watch(() => props.open, async (open) => {
  if (!open) return;
  pendingVoice.value = normalizeSelectedVoice(props.selectedVoice);
  activeTab.value = pendingVoice.value?.mode === "upload" ? "upload" : "platform";
  await (activeTab.value === "upload" ? audio.init() : initPlatform());
});

async function initPlatform() {
  platformPicker.reset();
  const result = await platformPicker.reload();
  if (!result.ok) emit("notify", result.message || "平台声音加载失败");
}
async function changeTab(value) {
  activeTab.value = value;
  await (value === "upload" ? audio.init() : initPlatform());
}
async function applyFilters() {
  const result = await platformPicker.reload();
  if (!result.ok) emit("notify", result.message || "平台声音加载失败");
}
async function reachEnd(event) {
  const picker = activeTab.value === "upload" ? audio.picker : platformPicker;
  const result = await picker.handleScroll(event);
  if (!result.ok) emit("notify", result.message || "加载失败");
}
function isPlatformSelected(item) {
  return pendingVoice.value?.mode === "platform" && pendingVoice.value?.voice_id === item.voice_id;
}
function isUploadSelected(item) {
  return pendingVoice.value?.mode === "upload" && pendingVoice.value?.audio_asset_id === (item.audio_asset_id || item.id);
}
function confirmSelection() {
  if (!pendingVoice.value) return emit("notify", activeTab.value === "upload" ? "请选择上传音频" : "请选择平台声音");
  emit("confirm", pendingVoice.value);
  emit("close");
}
</script>

<template>
  <HeygenPickerModalShell :open="open" title="选择声音" subtitle="平台声音和上传音频共用一个选择入口" :tabs="tabs" :active-tab="activeTab" :keyword="platformPicker.state.keyword" search-placeholder="搜索名称、voice_id、语言" :summary="summary" :show-toolbar="activeTab === 'platform'" :loading-more="activeTab === 'platform' ? platformPicker.state.loadingMore : audio.picker.state.loadingMore" @close="emit('close')" @change-tab="changeTab" @update:keyword="platformPicker.state.keyword = $event" @search="applyFilters" @reach-end="reachEnd">
    <template #filters><div class="w-32"><AppSelect v-model="platformPicker.filters.language" :options="heygenVoiceLanguageOptions" @update:model-value="applyFilters" /></div><div class="w-28"><AppSelect v-model="platformPicker.filters.gender" :options="heygenGenderOptions" @update:model-value="applyFilters" /></div><div class="w-36"><AppSelect v-model="platformPicker.filters.support_locale" :options="heygenVoiceLocaleOptions" @update:model-value="applyFilters" /></div></template>
    <UploadedAudioPanel v-if="activeTab === 'upload'" :controller="audio" :is-selected="isUploadSelected" @select="pendingVoice = normalizeUploadAudio($event)" />
    <div v-else-if="platformPicker.state.loading" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">正在加载平台声音...</div>
    <div v-else-if="!platformPicker.state.items.length" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">暂无可用平台声音</div>
    <div v-else class="space-y-3">
      <article v-for="item in platformPicker.state.items" :key="item.id" class="rounded-2xl border bg-white p-4 shadow-sm transition-all hover:border-primary/30 hover:shadow-md" :class="isPlatformSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'" @click="pendingVoice = normalizePlatformVoice(item)">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div class="min-w-0"><div class="flex items-center gap-2"><span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary/10 text-secondary"><Mic2 class="h-4.5 w-4.5" /></span><div class="min-w-0"><h3 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h3><p class="mt-0.5 truncate text-xs text-slate-400">{{ item.voice_id }}</p></div></div><div class="mt-3 flex flex-wrap gap-2"><span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] text-slate-500">{{ item.language || "未标注语言" }}</span><span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] text-slate-500">{{ item.gender === "unknown" || !item.gender ? "未知性别" : item.gender }}</span><span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] text-slate-500">Locale {{ item.support_locale ? "支持" : "不支持" }}</span><span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] text-slate-500">Pause {{ item.support_pause ? "支持" : "不支持" }}</span></div></div><div class="flex flex-col items-start gap-3 lg:items-end"><div class="max-w-full" @click.stop><audio v-if="item.preview_audio_url" :src="item.preview_audio_url" controls preload="none" class="h-8 w-64 max-w-full"></audio><span v-else class="text-xs text-slate-400">暂无试听</span></div><span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="isPlatformSelected(item) ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'">{{ isPlatformSelected(item) ? "已选择" : "点击选择" }}</span></div></div>
      </article>
    </div>
    <template #footer><div class="flex items-center justify-between gap-3"><p class="text-xs text-slate-400">{{ pendingVoice?.name ? `已选：${pendingVoice.name}` : "请选择 1 个声音或音频" }}</p><div class="flex items-center gap-2"><button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button><button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white hover:bg-secondary" @click="confirmSelection">确认选择</button></div></div></template>
  </HeygenPickerModalShell>
</template>
