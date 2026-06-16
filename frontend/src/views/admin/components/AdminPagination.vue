<script setup>
import { totalPages } from "../adminFormatters.js";

const props = defineProps({
  state: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["change-page"]);
</script>

<template>
  <div class="flex items-center justify-center gap-3 text-xs text-slate-500">
    <button
      type="button"
      class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40"
      :disabled="props.state.page <= 1"
      @click="emit('change-page', -1)"
    >
      上一页
    </button>
    <span>{{ props.state.page }} / {{ totalPages(props.state) }}</span>
    <button
      type="button"
      class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40"
      :disabled="props.state.page >= totalPages(props.state)"
      @click="emit('change-page', 1)"
    >
      下一页
    </button>
  </div>
</template>
