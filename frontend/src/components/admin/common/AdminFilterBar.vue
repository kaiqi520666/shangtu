<script setup>
defineProps({
  total: {
    type: Number,
    default: 0,
  },
  totalLabel: {
    type: String,
    default: "条记录",
  },
});

const emit = defineEmits(["apply-filter"]);
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
    <slot />
    <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
    <span class="ml-auto text-xs text-slate-400">共 {{ total }} {{ totalLabel }}</span>
    <slot name="actions" />
  </div>
</template>
