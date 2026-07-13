<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
});
</script>

<template>
  <section class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4">
      <h2 class="text-sm font-black text-slate-800">{{ title }}</h2>
      <p class="mt-1 text-xs text-slate-400">{{ description }}</p>
    </div>
    <slot />
  </section>
</template>
