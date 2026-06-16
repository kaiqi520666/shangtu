<script setup>
import { LoaderCircle } from "lucide-vue-next";

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  cards: {
    type: Array,
    default: () => [],
  },
});
</script>

<template>
  <section class="space-y-5">
    <div v-if="loading" class="flex h-40 items-center justify-center text-sm text-slate-400">
      <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
      正在加载...
    </div>
    <div v-else class="grid gap-4 md:grid-cols-3">
      <div
        v-for="card in cards"
        :key="card.label"
        class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <div class="flex items-center justify-between">
          <p class="text-xs font-semibold text-slate-400">{{ card.label }}</p>
          <component :is="card.icon" class="h-4 w-4 text-primary" />
        </div>
        <p class="mt-3 text-2xl font-black text-slate-900">{{ card.value }}</p>
      </div>
    </div>
  </section>
</template>
