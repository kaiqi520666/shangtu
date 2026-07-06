<script setup>
import AppCheckbox from "@/components/ui/AppCheckbox.vue";

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  form: {
    type: Object,
    required: true,
  },
  saving: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["close", "submit"]);
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
    <div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-sm font-black text-slate-900">编辑翻译语言</h2>
        <button type="button" class="text-xs text-slate-400 hover:text-slate-700" @click="emit('close')">关闭</button>
      </div>

      <div class="space-y-3">
        <label class="block">
          <span class="text-xs font-bold text-slate-600">HeyGen 原始名</span>
          <input :value="form.name" type="text" disabled class="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-400" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">中文展示名</span>
          <input v-model="form.display_name_zh" type="text" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">排序</span>
          <input v-model.number="form.sort_order" type="number" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
        </label>
        <AppCheckbox v-model="form.enabled" label="启用语言" />
      </div>

      <div class="mt-5 flex justify-end gap-2">
        <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button>
        <button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-black text-white disabled:opacity-50" :disabled="saving" @click="emit('submit', form)">
          {{ saving ? "保存中..." : "保存" }}
        </button>
      </div>
    </div>
  </div>
</template>
