<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { LoaderCircle, RotateCcw, Sparkles, X } from "lucide-vue-next";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  label: {
    type: String,
    required: true,
  },
  placeholder: {
    type: String,
    default: "",
  },
  rows: {
    type: Number,
    default: 5,
  },
  actionLabel: {
    type: String,
    default: "AI 帮写",
  },
  loadingLabel: {
    type: String,
    default: "生成中...",
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  generateDraft: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue"]);

const draft = ref("");
const expanded = ref(false);
const loading = ref(false);
const hasDraft = computed(() => draft.value.trim().length > 0);
let controller = null;
let runId = 0;

function invalidateRequest() {
  runId += 1;
  controller?.abort();
  controller = null;
  loading.value = false;
}

function closeDraft() {
  invalidateRequest();
  draft.value = "";
  expanded.value = false;
}

async function requestDraft() {
  invalidateRequest();
  const currentRunId = runId;
  controller = new AbortController();
  const currentController = controller;
  draft.value = "";
  expanded.value = true;
  loading.value = true;

  try {
    const ok = await props.generateDraft({
      signal: currentController.signal,
      onChunk(content) {
        if (runId === currentRunId && controller === currentController) {
          draft.value += content;
        }
      },
    });
    if (runId === currentRunId && controller === currentController && !ok && !hasDraft.value) {
      expanded.value = false;
    }
  } finally {
    if (runId === currentRunId && controller === currentController) {
      loading.value = false;
      controller = null;
    }
  }
}

function confirmDraft() {
  if (loading.value || !hasDraft.value) return;
  const value = draft.value;
  closeDraft();
  emit("update:modelValue", value);
}

watch(() => props.modelValue, closeDraft);
onBeforeUnmount(invalidateRequest);
</script>

<template>
  <div>
    <div class="mb-1.5 flex items-center justify-between gap-3">
      <label class="text-xs font-bold text-slate-800">{{ label }}</label>
      <button
        type="button"
        data-testid="ai-action"
        class="flex shrink-0 cursor-pointer items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-primary shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="disabled || loading"
        @click="requestDraft"
      >
        <LoaderCircle v-if="loading" class="h-3.5 w-3.5 animate-spin" />
        <Sparkles v-else class="h-3.5 w-3.5" />
        {{ loading ? loadingLabel : actionLabel }}
      </button>
    </div>

    <textarea
      :value="modelValue"
      data-testid="ai-source"
      class="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-60"
      :rows="rows"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="emit('update:modelValue', $event.target.value)"
    ></textarea>

    <div v-if="expanded" data-testid="ai-draft-panel" class="mt-2 border-l-2 border-primary/30 pl-3">
      <div class="mb-1.5 flex items-center justify-between gap-3">
        <span class="text-xs font-semibold text-slate-600">预览草稿</span>
        <button
          type="button"
          class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          title="取消草稿"
          @click="closeDraft"
        >
          <X class="h-4 w-4" />
        </button>
      </div>
      <textarea
        v-model="draft"
        data-testid="ai-draft"
        class="w-full resize-none rounded-xl border border-primary/20 bg-white p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary"
        :rows="rows"
      ></textarea>
      <div class="mt-2 flex justify-end gap-2">
        <button
          type="button"
          data-testid="ai-retry"
          class="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:border-primary/30 hover:text-primary"
          @click="requestDraft"
        >
          <RotateCcw class="h-3.5 w-3.5" />
          重新生成
        </button>
        <button
          type="button"
          data-testid="ai-confirm"
          class="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="loading || !hasDraft"
          @click="confirmDraft"
        >
          确认覆盖
        </button>
      </div>
    </div>
  </div>
</template>
