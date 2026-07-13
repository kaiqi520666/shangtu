<script setup>
import { Download, ImageOff, LayoutGrid, LoaderCircle, Search } from "lucide-vue-next";
import { taskMediaTypeOptions } from "@/constants/admin.js";
import AppPagination from "@/components/ui/AppPagination.vue";
import AssetCardGrid from "@/components/assets/AssetCardGrid.vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AppTabNav from "@/components/ui/AppTabNav.vue";
import { scenarioIcons as generationScenarioIcons, scenarioTabs } from "@/constants/scenarios.js";

defineProps({
  state: { type: Object, required: true },
  allSelected: { type: Boolean, default: false },
  selectedCount: { type: Number, default: 0 },
  downloading: { type: Boolean, default: false },
  preview: { type: Object, default: null },
  scenarioLabel: { type: Function, required: true },
  metaLabel: { type: Function, required: true },
});
const emit = defineEmits(["query", "change-scenario", "toggle-all", "toggle-card", "download", "batch-download", "preview", "change-page", "close-preview"]);

const scenarioIcons = {
  "": LayoutGrid,
  ...generationScenarioIcons,
};
</script>

<template>
  <section class="space-y-4">
    <header class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-base font-bold text-slate-800">管理资产</h2>
          <p class="mt-1 text-xs text-slate-400">查看所有用户已生成完成的图片和视频资产</p>
        </div>
        <div class="flex items-center gap-3">
          <AppCheckbox :model-value="allSelected" label="全选" size="sm" :disabled="state.items.length === 0" @change="emit('toggle-all')" />
          <button type="button" class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40" :disabled="selectedCount === 0 || downloading" @click="emit('batch-download')">
            <LoaderCircle v-if="downloading" class="h-3.5 w-3.5 animate-spin" />
            <Download v-else class="h-3.5 w-3.5" />
            {{ downloading ? "下载中..." : `下载 (${selectedCount})` }}
          </button>
          <span class="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-bold text-primary">共 {{ state.total }} 个</span>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <div class="relative min-w-72 flex-1">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-300" />
          <input v-model="state.keyword" type="text" class="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-8 pr-3 text-xs outline-none transition-colors focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary" placeholder="搜索邮箱、任务ID、标题或上游ID" @keyup.enter="emit('query')" />
        </div>
        <div class="w-36"><AppSelect v-model="state.mediaType" :options="taskMediaTypeOptions" @update:model-value="emit('query')" /></div>
        <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-secondary" @click="emit('query')">查询</button>
      </div>
      <AppTabNav :tabs="scenarioTabs" :active-key="state.scenario" :icons="scenarioIcons" @change="emit('change-scenario', $event)" />
    </header>

    <div class="min-h-[420px] rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div v-if="state.loading && state.items.length === 0" class="flex flex-col items-center justify-center py-20">
        <LoaderCircle class="h-8 w-8 animate-spin text-primary" /><span class="mt-3 text-sm text-slate-500">加载中...</span>
      </div>
      <div v-else-if="!state.loading && state.items.length === 0" class="flex flex-col items-center justify-center py-20">
        <ImageOff class="h-12 w-12 text-slate-300" /><p class="mt-3 text-sm text-slate-500">暂无资产</p><p class="mt-1 text-xs text-slate-400">用户完成图片或视频生成后，资源将出现在这里</p>
      </div>
      <AssetCardGrid v-else :cards="state.items" :scenario-label="scenarioLabel" :meta-label="metaLabel" :downloading="downloading" :show-delete="false" @toggle-card="emit('toggle-card', $event)" @download-card="emit('download', $event)" @zoom-card="emit('preview', $event)" />
    </div>
    <AppPagination :state="state" @change-page="emit('change-page', $event)" />
    <AppModal :open="!!preview" panel-class="max-w-[90vw] max-h-[90vh] w-auto" @close="emit('close-preview')">
      <div v-if="preview" class="flex items-center justify-center p-2">
        <video v-if="preview.mediaType === 'video'" :src="preview.dataUrl" class="max-h-[85vh] max-w-full object-contain" controls autoplay playsinline></video>
        <img v-else :src="preview.previewUrl || preview.resultUrl || preview.dataUrl" referrerpolicy="no-referrer" class="max-h-[85vh] max-w-full object-contain" alt="资产预览" />
      </div>
    </AppModal>
  </section>
</template>
