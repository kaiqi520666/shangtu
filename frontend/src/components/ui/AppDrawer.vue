<script setup>
import { X } from 'lucide-vue-next'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close'])
</script>

<template>
  <div v-if="open" class="fixed inset-y-0 right-0 z-40 flex w-96 max-w-full flex-col overflow-hidden border-l border-slate-200 bg-white shadow-2xl">
    <div class="flex items-center justify-between border-b border-slate-200 bg-slate-50/50 p-4">
      <div>
        <h3 class="text-sm font-bold text-slate-800">{{ title }}</h3>
        <p v-if="subtitle" class="text-xs text-slate-500">{{ subtitle }}</p>
      </div>
      <button type="button" class="text-slate-400 transition-colors hover:text-slate-600" @click="emit('close')">
        <X class="h-5 w-5" />
      </button>
    </div>
    <div class="flex-1 overflow-y-auto p-4">
      <slot />
    </div>
  </div>
</template>
