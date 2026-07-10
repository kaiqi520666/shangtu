<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: "",
  },
  tone: {
    type: String,
    default: "default",
    validator: (value) => ["default", "muted"].includes(value),
  },
  divider: {
    type: Boolean,
    default: true,
  },
});
</script>

<template>
  <section
    class="space-y-4 p-5"
    :class="[
      tone === 'muted' ? 'bg-slate-50/40' : 'bg-white',
      divider ? 'border-b border-slate-100' : '',
    ]"
  >
    <header class="flex flex-wrap items-start justify-between gap-x-3 gap-y-2">
      <div class="min-w-0 flex-1">
        <div class="flex min-w-0 flex-wrap items-center gap-x-1.5 gap-y-1">
          <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-primary"></span>
          <h2 class="text-xs font-bold text-slate-800">{{ title }}</h2>
          <slot name="meta" />
        </div>
        <p v-if="description" class="mt-1 text-xs leading-relaxed text-slate-400">{{ description }}</p>
      </div>
      <div v-if="$slots.actions" class="flex shrink-0 items-center gap-2">
        <slot name="actions" />
      </div>
    </header>

    <slot />
  </section>
</template>
