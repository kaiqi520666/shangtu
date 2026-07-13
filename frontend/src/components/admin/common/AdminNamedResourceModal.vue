<script setup>
import { reactive, watch } from "vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  saving: { type: Boolean, default: false },
  title: { type: String, required: true },
  nameLabel: { type: String, default: "名称" },
  enabledLabel: { type: String, required: true },
  statusField: { type: String, default: "enabled" },
});

const emit = defineEmits(["close", "submit"]);
const localForm = reactive({ id: "", name: "", sort_order: 0, status: true });

watch(
  () => [props.open, props.form?.id],
  () => {
    if (!props.open) return;
    Object.assign(localForm, {
      id: props.form?.id || "",
      name: props.form?.name || "",
      sort_order: Number(props.form?.sort_order || 0),
      status: Boolean(props.form?.[props.statusField]),
    });
  },
  { immediate: true },
);

function submit() {
  emit("submit", {
    id: localForm.id,
    name: localForm.name,
    sort_order: localForm.sort_order,
    [props.statusField]: localForm.status,
  });
}
</script>

<template>
  <AppModal :open="open" :title="title" panel-class="w-full max-w-lg" @close="emit('close')">
    <div class="space-y-4 p-5">
      <label class="block">
        <span class="text-xs font-bold text-slate-600">{{ nameLabel }}</span>
        <input v-model="localForm.name" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
      <label class="block">
        <span class="text-xs font-bold text-slate-600">排序</span>
        <input v-model.number="localForm.sort_order" type="number" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
      </label>
    </div>
    <template #footer>
      <AppCheckbox v-model="localForm.status" class="mr-auto" :label="enabledLabel" />
      <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button>
      <button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving" @click="submit">
        {{ saving ? "保存中..." : "保存" }}
      </button>
    </template>
  </AppModal>
</template>
