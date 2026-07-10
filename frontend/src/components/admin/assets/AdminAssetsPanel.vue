<script setup>
import { Boxes, Download, FileVideo, ImageOff, Images, LayoutGrid, LoaderCircle, Search, Shirt, Sparkles, Video } from "lucide-vue-next";
import { taskMediaTypeOptions } from "@/constants/admin.js";
import AdminPagination from "@/components/admin/AdminPagination.vue";
import AssetCardGrid from "@/components/assets/AssetCardGrid.vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AppTabNav from "@/components/ui/AppTabNav.vue";

defineProps({
  controller: { type: Object, required: true },
});

const scenarioTabs = [
  { value: "", label: "全部" },
  { value: "product_suite", label: "商品套图" },
  { value: "product_image", label: "商品详情图" },
  { value: "outfit", label: "服饰穿搭" },
  { value: "free_image", label: "自由生图" },
  { value: "product_video", label: "商品视频" },
  { value: "free_video", label: "自由生视频" },
];
const scenarioIcons = {
  "": LayoutGrid,
  product_suite: Boxes,
  product_image: Images,
  outfit: Shirt,
  free_image: Sparkles,
  product_video: Video,
  free_video: FileVideo,
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
          <AppCheckbox :model-value="controller.allSelected.value" label="全选" size="sm" :disabled="controller.state.items.length === 0" @change="controller.toggleSelectAllCards" />
          <button type="button" class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40" :disabled="controller.selectedCardsCount.value === 0 || controller.downloading.value" @click="controller.batchDownload">
            <LoaderCircle v-if="controller.downloading.value" class="h-3.5 w-3.5 animate-spin" />
            <Download v-else class="h-3.5 w-3.5" />
            {{ controller.downloading.value ? "下载中..." : `下载 (${controller.selectedCardsCount.value})` }}
          </button>
          <span class="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-bold text-primary">共 {{ controller.state.total }} 个</span>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <div class="relative min-w-72 flex-1">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-300" />
          <input v-model="controller.state.keyword" type="text" class="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-8 pr-3 text-xs outline-none transition-colors focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary" placeholder="搜索邮箱、任务ID、标题或上游ID" @keyup.enter="controller.applyAssetsFilter" />
        </div>
        <div class="w-36"><AppSelect v-model="controller.state.mediaType" :options="taskMediaTypeOptions" @update:model-value="controller.applyAssetsFilter" /></div>
        <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-secondary" @click="controller.applyAssetsFilter">查询</button>
      </div>
      <AppTabNav :tabs="scenarioTabs" :active-key="controller.state.scenario" :icons="scenarioIcons" @change="controller.changeScenario" />
    </header>

    <div class="min-h-[420px] rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div v-if="controller.state.loading && controller.state.items.length === 0" class="flex flex-col items-center justify-center py-20">
        <LoaderCircle class="h-8 w-8 animate-spin text-primary" /><span class="mt-3 text-sm text-slate-500">加载中...</span>
      </div>
      <div v-else-if="!controller.state.loading && controller.state.items.length === 0" class="flex flex-col items-center justify-center py-20">
        <ImageOff class="h-12 w-12 text-slate-300" /><p class="mt-3 text-sm text-slate-500">暂无资产</p><p class="mt-1 text-xs text-slate-400">用户完成图片或视频生成后，资源将出现在这里</p>
      </div>
      <AssetCardGrid v-else :cards="controller.state.items" :scenario-label="controller.scenarioLabel" :meta-label="controller.metaLabel" :downloading="controller.downloading.value" :show-delete="false" @toggle-card="controller.toggleCardSelection" @download-card="controller.downloadSingleMedia" @zoom-card="controller.zoomCard.value = $event" />
    </div>
    <AdminPagination v-if="controller.state.total > controller.state.pageSize" :state="controller.state" @change-page="controller.changePage" />
    <AppModal :open="!!controller.zoomCard.value" panel-class="max-w-[90vw] max-h-[90vh] w-auto" @close="controller.zoomCard.value = null">
      <div v-if="controller.zoomCard.value" class="flex items-center justify-center p-2">
        <video v-if="controller.zoomCard.value.mediaType === 'video'" :src="controller.zoomCard.value.dataUrl" class="max-h-[85vh] max-w-full object-contain" controls autoplay playsinline></video>
        <img v-else :src="controller.zoomCard.value.previewUrl || controller.zoomCard.value.resultUrl || controller.zoomCard.value.dataUrl" referrerpolicy="no-referrer" class="max-h-[85vh] max-w-full object-contain" alt="资产预览" />
      </div>
    </AppModal>
  </section>
</template>
