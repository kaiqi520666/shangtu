<script setup>
import { computed, reactive, watch } from "vue";
import { productCatalogScenarioLabel } from "@/constants/admin.js";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";

const defaultForm = {
  id: "",
  scenario: "",
  item_id: "",
  name: "",
  description: "",
  strategy: "",
  default_count: null,
  max_count: null,
  enabled: true,
  sort: 0,
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
const isSuite = computed(() => localForm.scenario === "product_suite");

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
    enabled: Boolean(props.form?.enabled ?? defaultForm.enabled),
    sort: Number(props.form?.sort || 0),
    default_count: props.form?.default_count ?? null,
    max_count: props.form?.max_count ?? null,
  });
}

function submit() {
  emit("submit", { ...localForm });
}
</script>

<template>
  <AppModal
    :open="open"
    title="编辑商品目录"
    panel-class="w-full max-w-4xl"
    @close="emit('close')"
  >
    <div class="space-y-4 overflow-y-auto p-5">
      <div class="grid gap-3 md:grid-cols-4">
        <label class="block md:col-span-2">
          <span class="text-xs font-bold text-slate-600">名称</span>
          <input v-model="localForm.name" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">场景</span>
          <input :value="productCatalogScenarioLabel(localForm.scenario)" type="text" class="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500 outline-none" disabled />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">目录 ID</span>
          <input :value="localForm.item_id" type="text" class="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500 outline-none" disabled />
        </label>
      </div>

      <div class="grid gap-3 md:grid-cols-3">
        <label class="block">
          <span class="text-xs font-bold text-slate-600">排序</span>
          <input v-model.number="localForm.sort" type="number" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
        </label>
        <label v-if="isSuite" class="block">
          <span class="text-xs font-bold text-slate-600">默认张数</span>
          <input v-model.number="localForm.default_count" type="number" min="1" max="100" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
        </label>
        <label v-if="isSuite" class="block">
          <span class="text-xs font-bold text-slate-600">最大张数</span>
          <input v-model.number="localForm.max_count" type="number" min="1" max="100" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
        </label>
      </div>

      <label class="block">
        <span class="text-xs font-bold text-slate-600">展示描述</span>
        <textarea
          v-model="localForm.description"
          rows="4"
          class="mt-1 w-full resize-y rounded-xl border border-slate-200 px-3 py-2 text-xs leading-relaxed outline-none focus:border-primary"
        ></textarea>
      </label>

      <label class="block">
        <span class="text-xs font-bold text-slate-600">生成策略</span>
        <textarea
          v-model="localForm.strategy"
          rows="8"
          class="mt-1 w-full resize-y rounded-xl border border-slate-200 px-3 py-2 text-xs leading-relaxed outline-none focus:border-primary"
        ></textarea>
      </label>

      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <AppCheckbox v-model="localForm.enabled" label="启用目录项" />
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
