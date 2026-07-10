<script setup>
import { ref } from "vue";
import { LoaderCircle, PlayCircle, Trash2, UploadCloud } from "lucide-vue-next";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";

defineProps({ controller: { type: Object, required: true } });
const emit = defineEmits(["preview"]);
const fileInput = ref(null);

function formatDateTime(value) {
  if (!value) return "刚刚创建";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚创建";
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(date);
}

function statusText(status) {
  return { processing: "创建中", failed: "创建失败", done: "已完成" }[status] || "排队中";
}

function statusClass(status) {
  return { processing: "bg-amber-100 text-amber-700", failed: "bg-rose-100 text-rose-600", done: "bg-emerald-100 text-emerald-700" }[status] || "bg-slate-100 text-slate-500";
}
</script>

<template>
  <div class="space-y-4">
    <div class="rounded-2xl border border-sky-100 bg-sky-50/80 px-4 py-3"><p class="text-sm font-bold text-slate-800">上传 1 张清晰正面人像图</p></div>
    <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="controller.handleFileChange" />
    <ImageUploadSourcePanel :drag-over="controller.uploadDragOver.value" action-text="上传人物照片" hint-text="支持点击上传或拖拽上传，单次只上传 1 张图片" :icon="UploadCloud" local-button-text="选择照片" :show-asset-button="false" @upload="fileInput?.click()" @drag-over="controller.uploadDragOver.value = true" @drag-leave="controller.uploadDragOver.value = false" @drop="controller.handleDrop" />

    <div v-if="controller.previewUrl.value || controller.name.value" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid gap-4 lg:grid-cols-[180px_1fr]">
        <div class="overflow-hidden rounded-2xl bg-slate-100"><img v-if="controller.previewUrl.value" :src="controller.previewUrl.value" class="aspect-[4/5] w-full object-cover" alt="照片预览" /><div v-else class="flex aspect-[4/5] items-center justify-center text-xs text-slate-400">待上传照片</div></div>
        <div class="space-y-4">
          <label class="block"><span class="mb-1.5 block text-xs font-bold text-slate-700">数字人名称</span><input v-model="controller.name.value" type="text" maxlength="120" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary" placeholder="输入名称，方便后续选择" /></label>
          <div class="flex items-center justify-between gap-3"><button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="controller.resetUpload">清空</button><button type="button" class="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white hover:bg-secondary disabled:opacity-60" :disabled="controller.creating.value" @click="controller.create"><LoaderCircle v-if="controller.creating.value" class="h-4 w-4 animate-spin" />{{ controller.creating.value ? "创建中..." : "创建照片数字人" }}</button></div>
        </div>
      </div>
    </div>

    <section v-if="controller.taskItems.value.length" class="space-y-3">
      <div class="flex items-center justify-between"><h3 class="text-sm font-black text-slate-800">创建任务</h3><span class="text-xs text-slate-400">共 {{ controller.tasks.state.total }} 条</span></div>
      <article v-for="item in controller.taskItems.value" :key="item.id" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="flex items-start gap-4">
          <div class="relative w-24 shrink-0 overflow-hidden rounded-2xl bg-slate-100"><img v-if="item.preview_image_url" :src="item.preview_image_url" class="aspect-[4/5] w-full object-cover" alt="照片数字人任务预览" /><div v-else class="flex aspect-[4/5] items-center justify-center text-xs text-slate-400">无预览图</div><button v-if="item.preview_image_url || item.preview_video_url" type="button" class="absolute right-2 top-2 rounded-full bg-white/90 p-1 text-slate-600 shadow-sm hover:text-primary" @click="emit('preview', item)"><PlayCircle class="h-4 w-4" /></button></div>
          <div class="min-w-0 flex-1"><div class="flex flex-wrap items-center gap-2"><h4 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h4><span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="statusClass(item.status)">{{ statusText(item.status) }}</span></div><p class="mt-2 text-xs text-slate-400">创建时间：{{ formatDateTime(item.created_at) }}</p><p v-if="item.error_message" class="mt-2 text-xs text-rose-500">{{ item.error_message }}</p></div>
          <button v-if="item.status === 'failed'" type="button" class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-rose-500" :disabled="controller.deletingTaskId.value === item.id" title="删除失败任务" @click="controller.removeTask(item)"><LoaderCircle v-if="controller.deletingTaskId.value === item.id" class="h-3.5 w-3.5 animate-spin" /><Trash2 v-else class="h-3.5 w-3.5" /></button>
        </div>
      </article>
    </section>

    <section class="space-y-3">
      <div class="flex items-center justify-between"><h3 class="text-sm font-black text-slate-800">我的照片数字人</h3><span class="text-xs text-slate-400">共 {{ controller.avatars.state.total }} 个</span></div>
      <div v-if="controller.avatars.state.loading" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">正在加载照片数字人...</div>
      <div v-else-if="!controller.avatars.state.items.length" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">暂无可用照片数字人，先上传 1 张试试</div>
      <div v-else class="space-y-3">
        <article v-for="item in controller.avatars.state.items" :key="item.id" class="rounded-2xl border bg-white p-4 shadow-sm transition-all hover:border-primary/30 hover:shadow-md" :class="controller.isSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'" @click="controller.select(item)">
          <div class="flex items-start gap-4">
            <div class="relative w-24 shrink-0 overflow-hidden rounded-2xl bg-slate-100"><img v-if="item.preview_image_url" :src="item.preview_image_url" class="aspect-[4/5] w-full object-cover" alt="照片数字人预览" /><div v-else class="flex aspect-[4/5] items-center justify-center text-xs text-slate-400">无预览图</div><button v-if="item.preview_image_url || item.preview_video_url" type="button" class="absolute right-2 top-2 rounded-full bg-white/90 p-1 text-slate-600 shadow-sm hover:text-primary" @click.stop="emit('preview', item)"><PlayCircle class="h-4 w-4" /></button></div>
            <div class="min-w-0 flex-1"><div class="flex items-center gap-2"><h4 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h4><span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="controller.isSelected(item) ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'">{{ controller.isSelected(item) ? "已选择" : "点击选择" }}</span></div><p class="mt-2 truncate text-xs text-slate-400">avatar_id：{{ item.avatar_id }}</p><p class="mt-1 text-xs text-slate-400">创建时间：{{ formatDateTime(item.created_at) }}</p></div>
            <button type="button" class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-rose-500" :disabled="controller.deletingAssetId.value === item.id" title="删除照片数字人" @click.stop="controller.removeAvatar(item)"><LoaderCircle v-if="controller.deletingAssetId.value === item.id" class="h-3.5 w-3.5 animate-spin" /><Trash2 v-else class="h-3.5 w-3.5" /></button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
