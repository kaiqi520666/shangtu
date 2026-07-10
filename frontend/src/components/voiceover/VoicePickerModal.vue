<script setup>
import { computed, ref, watch } from "vue";
import { Mic2 } from "lucide-vue-next";
import { getVoiceoverVoices } from "@/api/voiceover.js";
import PickerModalShell from "@/components/ui/PickerModalShell.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { usePagedResourcePicker } from "@/composables/usePagedResourcePicker.js";

const props = defineProps({ open: { type: Boolean, default: false }, selectedVoice: { type: Object, default: null } });
const emit = defineEmits(["close", "confirm", "notify"]);
const pendingVoice = ref(null);
const categoryOptions = ref([{ value: "", label: "全部类型" }]);
const picker = usePagedResourcePicker({
  listApi: getVoiceoverVoices,
  defaultFilters: { category: "", supportsInstruct: "" },
  buildParams: ({ page, pageSize, keyword, filters }) => ({
    page,
    page_size: pageSize,
    keyword: keyword || undefined,
    category: filters.category || undefined,
    supports_instruct: filters.supportsInstruct === "true" ? true : undefined,
  }),
});
const instructOptions = [{ value: "", label: "全部能力" }, { value: "true", label: "支持表达指令" }];
const summary = computed(() => `共 ${picker.state.total} 个音色`);

watch(() => props.open, async (open) => {
  if (!open) return;
  pendingVoice.value = props.selectedVoice ? { ...props.selectedVoice } : null;
  picker.reset();
  const catalog = await getVoiceoverVoices({ page: 1, page_size: 1 });
  categoryOptions.value = [{ value: "", label: "全部类型" }, ...(catalog.data?.categories || []).map((value) => ({ value, label: value }))];
  const result = await picker.reload();
  if (!result.ok) emit("notify", result.message || "音色加载失败");
});

async function reload() {
  const result = await picker.reload();
  if (!result.ok) emit("notify", result.message || "音色加载失败");
}

function confirmSelection() {
  if (!pendingVoice.value) return emit("notify", "请选择一个音色");
  emit("confirm", pendingVoice.value);
  emit("close");
}
</script>

<template>
  <PickerModalShell :open="open" title="选择音色" subtitle="" :keyword="picker.state.keyword" search-placeholder="搜索名称、voice ID、特质或语言" :summary="summary" :loading-more="picker.state.loadingMore" @close="emit('close')" @update:keyword="picker.state.keyword = $event" @search="reload" @reach-end="picker.handleScroll">
    <template #filters>
      <div class="w-40"><AppSelect v-model="picker.filters.category" :options="categoryOptions" @update:model-value="reload" /></div>
      <div class="w-40"><AppSelect v-model="picker.filters.supportsInstruct" :options="instructOptions" @update:model-value="reload" /></div>
    </template>
    <div v-if="picker.state.loading" class="flex min-h-80 items-center justify-center text-sm text-slate-400">正在加载音色...</div>
    <div v-else-if="!picker.state.items.length" class="flex min-h-80 items-center justify-center text-sm text-slate-400">暂无可用音色</div>
    <div v-else class="grid gap-3 lg:grid-cols-2">
      <article v-for="item in picker.state.items" :key="item.id" role="button" tabindex="0" class="border bg-white p-4 transition-colors" :class="pendingVoice?.voice_id === item.voice_id ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200 hover:border-primary/40'" @click="pendingVoice = item" @keyup.enter="pendingVoice = item">
        <div class="flex items-start gap-3"><span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary"><Mic2 class="h-4 w-4" /></span><div class="min-w-0 flex-1"><div class="flex items-center justify-between gap-2"><h3 class="truncate text-sm font-bold text-slate-800">{{ item.name }}</h3><span class="text-[11px] text-slate-400">{{ item.category }}</span></div><p class="mt-0.5 truncate text-xs text-slate-400">{{ item.voice_id }}</p><p class="mt-2 text-xs text-slate-500">{{ item.trait }} · {{ item.age_range }} · {{ item.languages }}</p><div class="mt-3" @click.stop @keyup.stop><audio :src="item.preview_audio_url" controls preload="none" class="h-8 w-full"></audio></div><span v-if="item.supports_instruct" class="mt-2 inline-block rounded bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700">支持表达指令</span></div></div>
      </article>
    </div>
    <template #footer><div class="flex items-center justify-between gap-3"><p class="text-xs text-slate-400">{{ pendingVoice?.name ? `已选：${pendingVoice.name}` : '请选择一个音色' }}</p><div class="flex gap-2"><button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button><button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white" @click="confirmSelection">确认选择</button></div></div></template>
  </PickerModalShell>
</template>
