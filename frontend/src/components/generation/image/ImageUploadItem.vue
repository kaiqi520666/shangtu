<script setup>
import { CheckCircle2, LoaderCircle, Trash2 } from "lucide-vue-next";

defineProps({
  image: {
    type: [Object, String],
    required: true,
  },
  previewUrl: {
    type: String,
    required: true,
  },
  index: {
    type: Number,
    required: true,
  },
  altText: {
    type: String,
    required: true,
  },
  showMainAction: {
    type: Boolean,
    default: true,
  },
  isMain: {
    type: Boolean,
    default: false,
  },
  showBadge: {
    type: Boolean,
    default: false,
  },
  badgeText: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["preview", "set-main", "remove"]);
</script>

<template>
  <div
    class="group relative flex aspect-square cursor-zoom-in items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-slate-50 p-1 shadow-inner"
    @click="emit('preview')"
  >
    <img
      :src="previewUrl"
      class="max-h-full max-w-full rounded-lg object-contain transition-transform duration-300 group-hover:scale-105"
      :alt="altText"
    />

    <div
      v-if="image?.uploading"
      class="absolute inset-0 flex flex-col items-center justify-center gap-1 bg-white/70 text-xs font-semibold text-primary"
    >
      <LoaderCircle class="h-5 w-5 animate-spin" />
      <span>上传中...</span>
    </div>
    <div v-else-if="image?.error" class="absolute inset-x-0 bottom-0 bg-rose-500/85 px-2 py-1 text-center text-xs text-white">
      {{ image.error }}
    </div>

    <div class="absolute inset-0 flex items-center justify-center gap-1.5 bg-slate-900/60 opacity-0 transition-opacity group-hover:opacity-100">
      <button
        v-if="showMainAction"
        type="button"
        class="rounded border border-slate-100 bg-white p-1.5 text-xs text-slate-800 shadow transition-colors hover:bg-slate-100"
        :class="isMain ? 'border-primary text-primary' : ''"
        title="设为渲染主图"
        @click.stop="emit('set-main')"
      >
        <CheckCircle2 class="h-3.5 w-3.5" />
      </button>
      <button
        type="button"
        class="rounded border border-slate-100 bg-white p-1.5 text-rose-500 shadow transition-colors hover:bg-rose-50"
        title="删除"
        @click.stop="emit('remove')"
      >
        <Trash2 class="h-3.5 w-3.5" />
      </button>
    </div>
    <span
      v-if="showBadge"
      class="absolute bottom-1 right-1 rounded bg-primary px-1.5 py-0.5 text-xs font-bold text-white shadow-sm"
    >
      {{ badgeText }}
    </span>
  </div>
</template>
