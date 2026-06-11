<script setup>
import GeneratorHeader from '@/components/GeneratorHeader.vue'
import GeneratorSidebar from '@/components/GeneratorSidebar.vue'

defineProps({
  taskCount: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['open-queue', 'open-history'])
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-slate-50 text-slate-800">
    <GeneratorHeader :task-count="taskCount" @open-queue="emit('open-queue')" @open-history="emit('open-history')" />
    <div class="flex flex-1 overflow-hidden">
      <GeneratorSidebar />
      <main class="flex flex-1 overflow-hidden">
        <slot />
      </main>
    </div>
  </div>
</template>
