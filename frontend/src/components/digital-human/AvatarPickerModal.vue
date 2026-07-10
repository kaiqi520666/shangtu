<script setup>
import { computed, ref, watch } from "vue";
import { PlayCircle } from "lucide-vue-next";
import { getDigitalHumanAvatars } from "@/api/digitalHuman.js";
import HeygenPickerModalShell from "@/components/digital-human/HeygenPickerModalShell.vue";
import PhotoAvatarsPanel from "@/components/digital-human/PhotoAvatarsPanel.vue";
import AppModal from "@/components/ui/AppModal.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { normalizeAvatar, usePhotoAvatars } from "@/composables/digital-human/usePhotoAvatars.js";
import { useHeygenResourcePicker } from "@/composables/digital-human/useHeygenResourcePicker.js";
import { heygenAvatarOrientationOptions, heygenGenderOptions } from "@/constants/admin.js";

const props = defineProps({ open: { type: Boolean, default: false }, selectedAvatar: { type: Object, default: null } });
const emit = defineEmits(["close", "confirm", "notify"]);
const tabs = [{ value: "system", label: "系统数字人" }, { value: "photo", label: "照片数字人" }];
const avatarGenderOptions = heygenGenderOptions.filter((item) => item.value !== "unknown");
const activeTab = ref("system");
const pendingAvatar = ref(null);
const previewItem = ref(null);

function notifyError(message) {
  emit("notify", { type: "error", message });
}

const systemPicker = useHeygenResourcePicker({
  listApi: getDigitalHumanAvatars,
  defaultFilters: { gender: "", orientation: "" },
  buildParams: ({ page, pageSize, keyword, filters }) => ({ page, page_size: pageSize, keyword: keyword || undefined, gender: filters.gender || undefined, orientation: filters.orientation || undefined }),
});
const photo = usePhotoAvatars({ selectedAvatar: pendingAvatar, notifyError });
const summary = computed(() => activeTab.value === "system" ? `共 ${systemPicker.state.total} 个系统数字人` : `共 ${photo.avatars.state.total} 个照片数字人`);

watch(() => props.open, async (open) => {
  if (!open) {
    photo.stopPolling();
    photo.resetUpload();
    previewItem.value = null;
    return;
  }
  pendingAvatar.value = normalizeAvatar(props.selectedAvatar);
  activeTab.value = pendingAvatar.value?.source === "photo" ? "photo" : "system";
  await (activeTab.value === "photo" ? photo.init() : initSystem());
});

async function initSystem() {
  photo.stopPolling();
  systemPicker.reset();
  const result = await systemPicker.reload();
  if (!result.ok) notifyError(result.message || "系统数字人加载失败");
}

async function changeTab(value) {
  activeTab.value = value;
  await (value === "photo" ? photo.init() : initSystem());
}

async function applyFilters() {
  const result = await systemPicker.reload();
  if (!result.ok) notifyError(result.message || "系统数字人加载失败");
}

async function reachEnd(event) {
  if (activeTab.value === "photo") return photo.reachEnd(event);
  const result = await systemPicker.handleScroll(event);
  if (!result.ok) notifyError(result.message || "系统数字人加载失败");
}

function isSelected(item) {
  const next = normalizeAvatar(item);
  return Boolean(next && pendingAvatar.value?.avatar_id === next.avatar_id);
}

function confirmSelection() {
  if (!pendingAvatar.value) return notifyError("请选择数字人");
  emit("confirm", pendingAvatar.value);
  emit("close");
}
</script>

<template>
  <HeygenPickerModalShell :open="open" title="选择数字人" subtitle="" :tabs="tabs" :active-tab="activeTab" :keyword="systemPicker.state.keyword" search-placeholder="搜索名称、avatar_id、group_id" :summary="summary" :show-toolbar="activeTab === 'system'" :loading-more="activeTab === 'system' ? systemPicker.state.loadingMore : photo.avatars.state.loadingMore || photo.tasks.state.loadingMore" @close="emit('close')" @change-tab="changeTab" @update:keyword="systemPicker.state.keyword = $event" @search="applyFilters" @reach-end="reachEnd">
    <template #filters><div class="w-28"><AppSelect v-model="systemPicker.filters.gender" :options="avatarGenderOptions" @update:model-value="applyFilters" /></div><div class="w-28"><AppSelect v-model="systemPicker.filters.orientation" :options="heygenAvatarOrientationOptions" @update:model-value="applyFilters" /></div></template>

    <PhotoAvatarsPanel v-if="activeTab === 'photo'" :controller="photo" @preview="previewItem = $event" />
    <div v-else-if="systemPicker.state.loading" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">正在加载系统数字人...</div>
    <div v-else-if="!systemPicker.state.items.length" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">暂无可用系统数字人</div>
    <div v-else class="grid gap-4 md:grid-cols-3 xl:grid-cols-4">
      <article v-for="item in systemPicker.state.items" :key="item.id" class="cursor-pointer overflow-hidden rounded-2xl border bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md" :class="isSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'" @click="pendingAvatar = normalizeAvatar(item)">
        <div class="relative aspect-[4/5] bg-slate-100"><img v-if="item.preview_image_url" :src="item.preview_image_url" class="h-full w-full object-cover" alt="数字人预览" /><div v-else class="flex h-full items-center justify-center text-xs text-slate-400">无预览图</div><span v-if="isSelected(item)" class="absolute right-3 top-3 rounded-full bg-primary px-2.5 py-1 text-[11px] font-bold text-white">已选择</span></div>
        <div class="space-y-2 p-4"><div><h3 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h3><p class="mt-1 text-xs text-slate-400">{{ item.gender || "未知性别" }} / {{ item.preferred_orientation || "未标注方向" }}</p></div><p class="truncate text-[11px] text-slate-400" :title="item.avatar_id">avatar_id：{{ item.avatar_id }}</p><button v-if="item.preview_video_url || item.preview_image_url" type="button" class="inline-flex items-center gap-1.5 rounded-xl bg-primary/10 px-3 py-2 text-xs font-bold text-primary hover:text-secondary" @click.stop="previewItem = item"><PlayCircle class="h-4 w-4" />预览</button></div>
      </article>
    </div>

    <template #footer><div class="flex items-center justify-between gap-3"><p class="text-xs text-slate-400">{{ pendingAvatar?.name ? `已选：${pendingAvatar.name}` : "请选择 1 个数字人" }}</p><div class="flex items-center gap-2"><button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button><button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white hover:bg-secondary" @click="confirmSelection">确认数字人</button></div></div></template>
  </HeygenPickerModalShell>

  <AppModal :open="Boolean(previewItem)" title="数字人预览" panel-class="w-full max-w-3xl" @close="previewItem = null"><div v-if="previewItem" class="space-y-4 p-5"><video v-if="previewItem.preview_video_url" :src="previewItem.preview_video_url" class="max-h-[70vh] w-full rounded-xl bg-black object-contain" controls autoplay playsinline></video><img v-else-if="previewItem.preview_image_url" :src="previewItem.preview_image_url" class="max-h-[70vh] w-full rounded-xl bg-slate-100 object-contain" alt="数字人预览" /></div></AppModal>
</template>
