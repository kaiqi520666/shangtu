<script setup>
import { Clock3, Plus } from "lucide-vue-next";
import GeneratorWorkspaceShell from "@/components/generation/GeneratorWorkspaceShell.vue";
import VideoDemoCardGrid from "@/components/product-video/VideoDemoCardGrid.vue";
import { getVideoDemoType, getVideoCreditCost, videoSizeOptions } from "@/constants/productVideo.js";

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  creditCosts: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["select-type", "notify"]);

function getSizeLabel(value) {
  return videoSizeOptions.find((item) => item.value === value)?.label || value;
}
</script>

<template>
  <GeneratorWorkspaceShell content-class="p-6">
    <template #header>
      <div class="z-10 flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-6 shadow-sm backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <span class="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">商品视频</span>
          <div>
            <p class="text-xs font-black text-slate-900">{{ getVideoDemoType(settings.videoType).title }}</p>
            <p class="mt-0.5 text-xs text-slate-400">
              {{ getSizeLabel(settings.sizePreset) }} / {{ settings.resolution }} / {{ settings.duration }}秒
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-lg border border-primary/30 bg-white px-3 py-1.5 text-xs font-semibold text-primary transition-all hover:bg-primary/5"
            @click="emit('notify', '商品视频新建任务会在后端接入时开放')"
          >
            <Plus class="h-3.5 w-3.5 stroke-[2.5]" />
            新建任务
          </button>
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition-all hover:border-primary/40 hover:text-primary"
            @click="emit('notify', '商品视频生成记录会在后端接入时开放')"
          >
            <Clock3 class="h-3.5 w-3.5" />
            生成记录
          </button>
        </div>
      </div>
    </template>

    <div class="mx-auto max-w-7xl space-y-6">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 class="text-xl font-black tracking-normal text-slate-950">选择方向，预览商品视频效果</h1>
            <p class="mt-2 text-sm font-medium text-slate-500">
              右侧展示真实示例视频。第一版会根据方向自动决定上传方式，减少参数选择。
            </p>
          </div>
          <div class="rounded-2xl bg-slate-50 px-4 py-3 text-right">
            <p class="text-xs font-bold text-slate-400">预计消耗</p>
            <p class="mt-1 text-lg font-black text-primary">
              {{ getVideoCreditCost({ resolution: settings.resolution, duration: settings.duration, costs: creditCosts }) }} 积分
            </p>
          </div>
        </div>

        <VideoDemoCardGrid :active-type="settings.videoType" @select="emit('select-type', $event)" />
      </div>
    </div>
  </GeneratorWorkspaceShell>
</template>
