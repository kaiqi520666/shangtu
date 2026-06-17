<script setup>
import { Clock3, Plus } from "lucide-vue-next";
import GeneratorWorkspaceShell from "@/components/generation/GeneratorWorkspaceShell.vue";
import VideoDemoCardGrid from "@/components/product-video/VideoDemoCardGrid.vue";

const emit = defineEmits(["notify"]);
</script>

<template>
  <GeneratorWorkspaceShell content-class="p-6">
    <template #header>
      <div class="z-10 flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-6 shadow-sm backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <span class="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">商品视频</span>
          <div>
            <p class="text-xs font-black text-slate-900">视频示例预览</p>
            <p class="mt-0.5 text-xs text-slate-400">点击任意示例可直接播放</p>
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
        <div class="mb-6">
          <div>
            <h1 class="text-xl font-black tracking-normal text-slate-950">商品视频示例</h1>
            <p class="mt-2 text-sm font-medium text-slate-500">
              这里仅用于预览不同电商视频风格，左侧选择的视频方向才会影响生成设置。
            </p>
          </div>
        </div>

        <VideoDemoCardGrid />
      </div>
    </div>
  </GeneratorWorkspaceShell>
</template>
