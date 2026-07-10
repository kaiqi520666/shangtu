<script setup>
import { reactive, watch } from "vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";

const defaultForm = {
  id: "",
  name: "",
  sort_order: 0,
  active: true,
};

const props = defineProps({
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

const localForm = reactive({ ...defaultForm });

watch(
  () => props.open,
  (open) => {
    if (open) syncLocalForm();
  },
  { immediate: true },
);

watch(
  () => props.form?.id,
  () => {
    if (props.open) syncLocalForm();
  },
);

function syncLocalForm() {
  Object.assign(localForm, {
    ...defaultForm,
    ...props.form,
    active: Boolean(props.form?.active ?? defaultForm.active),
    sort_order: Number(props.form?.sort_order || 0),
  });
}

function submit() {
  emit("submit", { ...localForm });
}
</script>

<template>
  <AppModal :open="open" title="编辑系统模特" panel-class="w-full max-w-lg" @close="emit('close')">
    <div class="space-y-4 p-5">
      <label class="block">
        <span class="text-xs font-bold text-slate-600">模特名称</span>
        <input v-model="localForm.name" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
      <label class="block">
        <span class="text-xs font-bold text-slate-600">排序</span>
        <input v-model.number="localForm.sort_order" type="number" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <AppCheckbox v-model="localForm.active" label="启用模特" />
        <div class="flex gap-2">
          <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button>
          <button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving" @click="submit">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </AppModal>
</template>
