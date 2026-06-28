<script setup>
import { FolderOpen, ImagePlus } from "lucide-vue-next";

defineProps({
  actionText: {
    type: String,
    required: true,
  },
  hintText: {
    type: String,
    required: true,
  },
  dragOver: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["upload", "asset", "drag-over", "drag-leave", "drop"]);
</script>

<template>
  <div
    class="rounded-2xl border border-dashed bg-white p-3 transition-all duration-300"
    :class="
      dragOver
        ? 'border-primary bg-primary/5 shadow-sm'
        : 'border-slate-300 hover:border-primary/40 hover:bg-slate-50'
    "
    @dragover.prevent="emit('drag-over')"
    @dragleave.prevent="emit('drag-leave')"
    @drop.prevent="emit('drop', $event)"
  >
    <div class="flex items-center gap-3 rounded-xl bg-slate-50 px-3 py-3">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-primary shadow-sm">
        <ImagePlus class="h-5 w-5" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="truncate text-sm font-black text-slate-800">{{ actionText }}</p>
        <p class="mt-0.5 text-xs leading-relaxed text-slate-500">{{ hintText }}</p>
      </div>
    </div>

    <div class="mt-3 grid grid-cols-2 gap-2">
      <button
        type="button"
        class="inline-flex h-11 min-w-0 items-center justify-center gap-2 rounded-xl border border-primary/20 bg-primary px-3 text-xs font-black text-white shadow-sm transition-colors hover:bg-primary/90"
        @click="emit('upload')"
      >
        <ImagePlus class="h-4 w-4 shrink-0" />
        <span class="truncate">本地上传</span>
      </button>
      <button
        type="button"
        class="inline-flex h-11 min-w-0 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-xs font-black text-slate-700 shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
        @click="emit('asset')"
      >
        <FolderOpen class="h-4 w-4 shrink-0" />
        <span class="truncate">资产库选择</span>
      </button>
    </div>
  </div>
</template>
