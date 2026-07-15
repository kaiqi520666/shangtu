<script setup>
import { Download, LoaderCircle, Pencil, Trash2, TriangleAlert } from "lucide-vue-next";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";

const props = defineProps({
  card: { type: Object, required: true },
  label: { type: String, required: true },
  metaText: { type: String, default: "" },
  mediaLabel: { type: String, required: true },
  downloading: { type: Boolean, default: false },
  editable: { type: Boolean, default: false },
  aspectClass: { type: String, default: "aspect-square" },
});

const emit = defineEmits(["toggle", "download", "edit", "activate", "delete"]);

function isFailed() {
  return props.card.status === "failed" || props.card.status === "timeout";
}

function isRunning() {
  return props.card.status === "pending" || props.card.status === "processing";
}

function canDownload() {
  return props.card.status === "done" && Boolean(props.card.dataUrl) && !props.card.downloading;
}

function failureReason() {
  if (props.card.errorMessage) return props.card.errorMessage;
  return props.card.status === "timeout" ? "生成超时，请稍后重试" : "生成失败，请稍后重试";
}
</script>

<template>
  <article class="group relative flex flex-col justify-between overflow-hidden rounded-lg border bg-white shadow-sm" :class="card.selected ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'">
    <div class="absolute left-2.5 right-20 top-2.5 z-10 flex min-w-0 items-center gap-2">
      <AppCheckbox :model-value="card.selected" @change="emit('toggle', card.id)" />
      <span class="min-w-0 truncate rounded-full border border-slate-200 bg-white/90 px-2 py-0.5 text-xs font-bold text-slate-700 shadow-sm backdrop-blur-sm">{{ label }}</span>
    </div>

    <div class="absolute right-2.5 top-2.5 z-10 flex gap-1.5">
      <button v-if="editable && card.status === 'done' && card.dataUrl" type="button" class="rounded-md border border-slate-200 bg-white/95 p-1.5 text-slate-600 shadow-sm hover:text-primary" :title="`编辑${mediaLabel}`" @click="emit('edit', card)"><Pencil class="h-3.5 w-3.5" /></button>
      <button v-if="!isRunning()" type="button" class="rounded-md border border-slate-200 bg-white/95 p-1.5 text-slate-600 shadow-sm hover:text-rose-500" :title="`删除${mediaLabel}`" @click="emit('delete', card)"><Trash2 class="h-3.5 w-3.5" /></button>
    </div>

    <div role="button" tabindex="0" class="relative flex cursor-pointer items-center justify-center overflow-hidden bg-slate-100" :class="aspectClass" @click="canDownload() && emit('activate', card)" @keyup.enter="canDownload() && emit('activate', card)">
      <slot v-if="card.dataUrl" name="preview" :card="card" />
      <div v-else-if="isFailed()" class="flex flex-col items-center gap-1.5 px-4 text-center text-rose-500">
        <TriangleAlert class="h-7 w-7" /><span class="text-xs font-semibold">生成失败</span>
      </div>
      <div v-else class="flex flex-col items-center gap-2 text-primary">
        <LoaderCircle class="h-7 w-7 animate-spin" />
        <span class="text-xs font-semibold text-slate-500">{{ card.status === 'processing' ? '生成中...' : '排队中...' }}</span>
        <span v-if="card.stalledWarning" class="max-w-[11rem] px-4 text-center text-[11px] font-medium leading-snug text-amber-600">{{ card.stalledWarning }}</span>
      </div>
      <div v-if="isRunning() && card.dataUrl" class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/70 backdrop-blur-[2px]">
        <LoaderCircle class="h-7 w-7 animate-spin text-primary" /><span class="text-xs font-semibold text-slate-600">重新生成中...</span>
      </div>
    </div>

    <div class="flex flex-1 flex-col justify-between border-t border-slate-100 bg-white p-3">
      <div v-if="isFailed()" class="mb-1.5">
        <p class="line-clamp-2 text-[11px] font-medium leading-snug text-rose-500" :title="failureReason()">原因：{{ failureReason() }}</p>
      </div>
      <div class="flex items-center justify-between gap-2">
        <div class="min-w-0">
          <span class="block truncate text-xs font-medium text-slate-500">{{ metaText }}</span>
          <span v-if="card.creditCost" class="mt-1 block text-[11px] font-semibold text-slate-400">消耗 {{ card.creditCost }} 积分</span>
        </div>
        <button v-if="!isRunning()" type="button" class="flex shrink-0 items-center gap-1 text-xs" :class="canDownload() ? 'font-bold text-primary hover:text-secondary' : 'cursor-not-allowed font-semibold text-slate-300'" :disabled="downloading || card.downloading || !canDownload()" @click.stop="emit('download', card)">
          {{ card.downloading ? "准备中" : `下载${mediaLabel}` }}
          <LoaderCircle v-if="card.downloading" class="h-3 w-3 animate-spin" /><Download v-else class="h-3 w-3" />
        </button>
        <span v-else class="shrink-0 text-xs font-medium text-slate-400">{{ card.status === 'processing' ? '生成中...' : '排队中...' }}</span>
      </div>
    </div>
  </article>
</template>
