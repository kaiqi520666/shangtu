<script setup>
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";

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
  <AppModal :open="open" title="编辑系统模特" panel-class="w-full max-w-lg" @close="emit('close')">
    <div class="space-y-4 p-5">
      <label class="block">
        <span class="text-xs font-bold text-slate-600">模特名称</span>
        <input v-model="form.name" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
      <label class="block">
        <span class="text-xs font-bold text-slate-600">排序</span>
        <input v-model.number="form.sort_order" type="number" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <AppCheckbox v-model="form.active" label="启用模特" />
        <div class="flex gap-2">
          <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button>
          <button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving" @click="emit('submit')">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </AppModal>
</template>
