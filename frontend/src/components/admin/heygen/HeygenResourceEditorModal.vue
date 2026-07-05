<script setup>
import { reactive, watch } from "vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";

const defaultForm = {
  id: "",
  name: "",
  sort_order: 0,
  enabled: true,
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
  title: {
    type: String,
    default: "编辑资源",
  },
  enabledLabel: {
    type: String,
    default: "启用资源",
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
    sort_order: Number(props.form?.sort_order || 0),
    enabled: Boolean(props.form?.enabled ?? defaultForm.enabled),
  });
}

function submit() {
  emit("submit", { ...localForm });
}
</script>

<template>
  <AppModal :open="open" :title="title" panel-class="w-full max-w-lg" @close="emit('close')">
    <div class="space-y-4 p-5">
      <label class="block">
        <span class="text-xs font-bold text-slate-600">名称</span>
        <input v-model="localForm.name" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
      <label class="block">
        <span class="text-xs font-bold text-slate-600">排序</span>
        <input v-model.number="localForm.sort_order" type="number" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <AppCheckbox v-model="localForm.enabled" :label="enabledLabel" />
        <div class="flex gap-2">
          <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button>
          <button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving" @click="submit">
            {{ saving ? "保存中..." : "保存" }}
          </button>
        </div>
      </div>
    </div>
  </AppModal>
</template>
