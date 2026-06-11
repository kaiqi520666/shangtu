<script setup>
defineProps({
  contentClass: {
    type: String,
    default: 'p-6',
  },
})
</script>

<template>
  <section class="relative flex h-full flex-1 flex-col overflow-hidden bg-slate-50">
    <slot name="header" />
    <div class="relative flex-1 overflow-y-auto" :class="contentClass">
      <slot />
    </div>
  </section>
</template>
