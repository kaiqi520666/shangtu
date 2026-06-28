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
    class="flex aspect-square flex-col rounded-xl border border-dashed p-2 transition-all duration-300"
    :class="
      dragOver
        ? 'border-primary bg-primary/10 shadow-sm'
        : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100/50'
    "
    @dragover.prevent="emit('drag-over')"
    @dragleave.prevent="emit('drag-leave')"
    @drop.prevent="emit('drop', $event)"
  >
    <button
      type="button"
      class="flex min-h-0 flex-1 flex-col items-center justify-center rounded-lg px-2 text-center transition-colors hover:bg-white/70"
      @click="emit('upload')"
    >
      <ImagePlus class="mb-1 h-5 w-5 shrink-0 text-slate-400" />
      <span class="w-full truncate text-xs font-bold text-slate-600">{{ actionText }}</span>
      <span class="mt-0.5 w-full truncate text-xs text-slate-400">{{ hintText }}</span>
    </button>
    <button
      type="button"
      class="mt-2 inline-flex h-8 min-w-0 items-center justify-center gap-1 rounded-lg border border-slate-200 bg-white px-2 text-xs font-bold text-slate-600 shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
      @click="emit('asset')"
    >
      <FolderOpen class="h-3.5 w-3.5 shrink-0" />
      <span class="truncate">资产库</span>
    </button>
  </div>
</template>
