<script setup>
import { reactive, ref, watch } from "vue";
import { activeStatusLabel, activeStatusOptions, formatTime } from "@/constants/admin.js";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AdminPagination from "./AdminPagination.vue";

const props = defineProps({
  state: {
    type: Object,
    required: true,
  },
  uploadSaving: {
    type: Boolean,
    default: false,
  },
  uploadResetKey: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(["apply-filter", "change-page", "upload", "edit", "toggle", "delete"]);

const fileInput = ref(null);
const uploadDraft = reactive({
  name: "",
  sort_order: 0,
  file: null,
});

watch(
  () => props.uploadResetKey,
  () => {
    resetUploadForm();
  },
);

function handleFileChange(file) {
  uploadDraft.file = file;
  if (!uploadDraft.name && file?.name) {
    uploadDraft.name = file.name.replace(/\.[^.]+$/, "");
  }
}

function resetUploadForm() {
  uploadDraft.name = "";
  uploadDraft.sort_order = 0;
  uploadDraft.file = null;
  if (fileInput.value) {
    fileInput.value.value = "";
  }
}

function submitUpload() {
  emit("upload", {
    name: uploadDraft.name,
    sortOrder: uploadDraft.sort_order,
    file: uploadDraft.file,
  });
}
</script>

<template>
  <section class="space-y-4">
    <div class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="mb-3 flex items-center justify-between">
        <div>
          <h2 class="text-sm font-black text-slate-800">上传系统模特</h2>
          <p class="mt-1 text-xs text-slate-400">上传后所有用户都可以在服饰穿搭里选择。</p>
        </div>
      </div>
      <div class="grid gap-3 md:grid-cols-[1fr_1fr_0.6fr_auto]">
        <input v-model="uploadDraft.name" type="text" class="rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" placeholder="模特名称" />
        <input ref="fileInput" type="file" accept="image/*" class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-2.5 file:py-1 file:text-xs file:font-bold file:text-slate-600" @change="handleFileChange($event.target.files?.[0] || null)" />
        <input v-model.number="uploadDraft.sort_order" type="number" class="rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" placeholder="排序" />
        <button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="uploadSaving" @click="submitUpload">
          {{ uploadSaving ? '上传中...' : '上传' }}
        </button>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <input v-model="state.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索名称、OSS key 或 URL" @keyup.enter="emit('apply-filter')" />
      <div class="w-32">
        <AppSelect v-model="state.active" :options="activeStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个系统模特</span>
    </div>

    <div class="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
      <div v-if="state.loading" class="col-span-full rounded-xl border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-400">加载中...</div>
      <div v-else-if="!state.items.length" class="col-span-full rounded-xl border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-400">暂无系统模特</div>
      <article v-for="model in state.items" v-else :key="model.id" class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div class="aspect-[3/4] bg-slate-100">
          <img :src="model.image_url" class="h-full w-full object-cover" />
        </div>
        <div class="space-y-2 p-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <h3 class="truncate text-sm font-black text-slate-800">{{ model.name }}</h3>
              <p class="mt-0.5 text-xs text-slate-400">排序 {{ model.sort_order }}</p>
            </div>
            <AppCheckbox :model-value="model.active" :label="activeStatusLabel(model.active)" @change="emit('toggle', model)" />
          </div>
          <p class="truncate text-[11px] text-slate-400" :title="model.object_key">{{ model.object_key }}</p>
          <p class="text-[11px] text-slate-400">{{ formatTime(model.created_at) }}</p>
          <div class="flex gap-2">
            <button type="button" class="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('edit', model)">编辑</button>
            <button type="button" class="flex-1 rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-bold text-rose-600 hover:bg-rose-50" @click="emit('delete', model)">停用</button>
          </div>
        </div>
      </article>
    </div>

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
