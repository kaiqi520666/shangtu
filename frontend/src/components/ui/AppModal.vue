<script setup>
import { X } from 'lucide-vue-next'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  panelClass: {
    type: String,
    default: 'w-full max-w-lg',
  },
})

const emit = defineEmits(['close'])
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-6 backdrop-blur-sm" @click="emit('close')">
    <div class="flex max-h-[90vh] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl" :class="panelClass" @click.stop>
      <div v-if="title || $slots.header" class="flex shrink-0 items-center justify-between border-b border-slate-100 bg-slate-50/50 px-5 py-4">
        <slot name="header">
          <div>
            <h3 class="text-sm font-bold text-slate-800">{{ title }}</h3>
            <p v-if="subtitle" class="text-xs text-slate-500">{{ subtitle }}</p>
          </div>
        </slot>
        <button type="button" class="text-slate-400 transition-colors hover:text-slate-600" @click="emit('close')">
          <X class="h-5 w-5" />
        </button>
      </div>
      <slot />
    </div>
  </div>
</template>
