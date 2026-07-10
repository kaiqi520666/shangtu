<script setup>
import { ref } from "vue";
import { LoaderCircle, Trash2, UploadCloud } from "lucide-vue-next";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";

defineProps({ controller: { type: Object, required: true }, isSelected: { type: Function, required: true } });
const emit = defineEmits(["select"]);
const fileInput = ref(null);

function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds || 0));
  if (!total) return "时长未知";
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}
function formatSize(size) {
  const value = Number(size || 0);
  if (value <= 0) return "";
  return value < 1024 * 1024 ? `${Math.max(1, Math.round(value / 1024))} KB` : `${(value / (1024 * 1024)).toFixed(1)} MB`;
}
function formatDate(value) {
  if (!value) return "刚刚上传";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "刚刚上传" : new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(date);
}
</script>

<template>
  <div class="space-y-4">
    <div class="rounded-2xl border border-sky-100 bg-sky-50/80 px-4 py-3"><p class="text-sm font-bold text-slate-800">上传 1 个音频文件作为口型驱动</p><p class="mt-1 text-xs leading-relaxed text-slate-500">使用上传音频后，将不再填写口播文案，系统会直接按音频驱动数字人口型。</p></div>
    <input ref="fileInput" type="file" accept="audio/*" class="hidden" @change="controller.handleFileChange" />
    <ImageUploadSourcePanel :drag-over="controller.uploadDragOver.value" action-text="上传音频" hint-text="支持点击上传或拖拽上传，单次只上传 1 个文件" :icon="UploadCloud" local-button-text="选择音频" :show-asset-button="false" @upload="fileInput?.click()" @drag-over="controller.uploadDragOver.value = true" @drag-leave="controller.uploadDragOver.value = false" @drop="controller.handleDrop" />
    <div v-if="controller.uploading.value" class="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-5 text-sm text-slate-500"><LoaderCircle class="h-4 w-4 animate-spin text-primary" />上传中...</div>
    <section class="space-y-3">
      <div class="flex items-center justify-between"><h3 class="text-sm font-black text-slate-800">我的音频</h3><span class="text-xs text-slate-400">共 {{ controller.picker.state.total }} 条</span></div>
      <div v-if="controller.picker.state.loading" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">正在加载上传音频...</div>
      <div v-else-if="!controller.picker.state.items.length" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">暂无可用音频，先上传 1 个试试</div>
      <div v-else class="space-y-3">
        <article v-for="item in controller.picker.state.items" :key="item.id" class="rounded-2xl border bg-white p-4 shadow-sm transition-all hover:border-primary/30 hover:shadow-md" :class="isSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'" @click="emit('select', item)">
          <div class="flex items-start justify-between gap-3"><div class="min-w-0 flex-1"><div class="flex items-center gap-2"><span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary/10 text-secondary"><UploadCloud class="h-4.5 w-4.5" /></span><div class="min-w-0"><h3 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h3><p class="mt-0.5 text-xs text-slate-400">{{ formatDuration(item.duration_seconds) }}<span v-if="formatSize(item.size)"> · {{ formatSize(item.size) }}</span></p></div></div><p class="mt-3 text-[11px] text-slate-400">上传时间：{{ formatDate(item.created_at) }}</p><div class="mt-3" @click.stop><audio :src="item.audio_url" controls preload="none" class="h-10 w-full"></audio></div></div>
            <div class="flex shrink-0 flex-col items-end gap-2"><button type="button" class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-rose-500" :disabled="controller.deletingId.value === item.id" title="删除音频" @click.stop="controller.remove(item)"><LoaderCircle v-if="controller.deletingId.value === item.id" class="h-3.5 w-3.5 animate-spin" /><Trash2 v-else class="h-3.5 w-3.5" /></button><span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="isSelected(item) ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'">{{ isSelected(item) ? "已选择" : "点击选择" }}</span></div></div>
        </article>
      </div>
    </section>
  </div>
</template>
