<script setup>
import { computed, reactive, watch } from "vue";
import {
  promptEditorScenarioOptions,
  promptModelOptions,
  promptPurposeOptions,
} from "@/constants/admin.js";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";
import AppSelect from "@/components/ui/AppSelect.vue";

const defaultForm = {
  id: "",
  scenario: "",
  purpose: "image_generate",
  platform: "",
  type_id: "",
  model: "gpt-image-2",
  name: "",
  content: "",
  version: 1,
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
const title = computed(() => (localForm.id ? "编辑提示词模板" : "新增提示词模板"));
const typeIdLabel = computed(() => {
  if (localForm.scenario === "product_video") return "视频方向 type_id";
  if (localForm.scenario === "product_suite") return "套图类型 type_id";
  if (localForm.scenario === "product_image") return "详情图种 type_id";
  if (localForm.scenario === "outfit") return "穿搭场景 type_id";
  return "方向 / 图种 type_id";
});
const typeIdPlaceholder = computed(() => (
  localForm.scenario === "product_video"
    ? "如 product_talk；留空表示商品视频通用规则"
    : "留空表示通用"
));

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
    ...(props.form || {}),
    active: Boolean(props.form?.active ?? defaultForm.active),
    version: Number(props.form?.version || defaultForm.version),
  });
}

function submit() {
  emit("submit", { ...localForm });
}
</script>

<template>
  <AppModal
    :open="open"
    :title="title"
    panel-class="w-full max-w-4xl"
    @close="emit('close')"
  >
    <div class="space-y-4 overflow-y-auto p-5">
      <div class="grid gap-3 md:grid-cols-4">
        <label class="block">
          <span class="text-xs font-bold text-slate-600">名称</span>
          <input v-model="localForm.name" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">用途</span>
          <AppSelect v-model="localForm.purpose" class="mt-1" :options="promptPurposeOptions.filter((item) => item.value)" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">模型</span>
          <AppSelect v-model="localForm.model" class="mt-1" :options="promptModelOptions.filter((item) => item.value)" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">版本</span>
          <input v-model.number="localForm.version" type="number" min="1" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" />
        </label>
      </div>

      <div class="grid gap-3 md:grid-cols-3">
        <label class="block">
          <span class="text-xs font-bold text-slate-600">场景</span>
          <AppSelect v-model="localForm.scenario" class="mt-1" :options="promptEditorScenarioOptions" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">平台</span>
          <input v-model="localForm.platform" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" placeholder="留空表示通用" />
        </label>
        <label class="block">
          <span class="text-xs font-bold text-slate-600">{{ typeIdLabel }}</span>
          <input v-model="localForm.type_id" type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-primary" :placeholder="typeIdPlaceholder" />
        </label>
      </div>

      <label class="block">
        <span class="text-xs font-bold text-slate-600">提示词内容</span>
        <textarea
          v-model="localForm.content"
          rows="14"
          class="mt-1 w-full resize-y rounded-xl border border-slate-200 px-3 py-2 text-xs leading-relaxed outline-none focus:border-primary"
        ></textarea>
      </label>

      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <AppCheckbox v-model="localForm.active" label="启用模板" />
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
