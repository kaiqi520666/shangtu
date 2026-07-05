<script setup>
defineProps({
  icon: {
    type: Object,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  actionText: {
    type: String,
    default: "",
  },
});
</script>

<template>
  <div class="flex min-h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 text-center">
    <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
      <component :is="icon" class="h-6 w-6" />
    </div>
    <p class="mt-4 text-sm font-black text-slate-800">{{ title }}</p>
    <p class="mt-2 max-w-md text-xs leading-relaxed text-slate-400">{{ description }}</p>
    <button v-if="actionText" type="button" disabled class="mt-4 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-400">
      {{ actionText }}
    </button>
  </div>
</template>
