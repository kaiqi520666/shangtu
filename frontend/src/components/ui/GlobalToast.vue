<script setup>
import { CheckCircle2, Info, X, XCircle } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast.js'

const toast = useToast()

function iconFor(type) {
  if (type === 'success') return CheckCircle2
  if (type === 'error') return XCircle
  return Info
}

function colorFor(type) {
  if (type === 'success') return 'border-primary/20 bg-primary/10 text-primary'
  if (type === 'error') return 'border-rose-200 bg-rose-50 text-rose-600'
  return 'border-sky-200 bg-sky-50 text-sky-600'
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed right-5 top-20 z-[80] flex w-80 max-w-[calc(100vw-40px)] flex-col gap-2">
      <div
        v-for="item in toast.toasts"
        :key="item.id"
        data-testid="global-toast"
        class="flex items-start gap-2 rounded-xl border bg-white px-3 py-3 text-xs font-medium shadow-lg backdrop-blur-sm"
        :class="colorFor(item.type)"
      >
        <component :is="iconFor(item.type)" class="mt-0.5 h-4 w-4 shrink-0" />
        <p class="min-w-0 flex-1 leading-5">{{ item.message }}</p>
        <button type="button" class="shrink-0 opacity-70 transition-opacity hover:opacity-100" @click="toast.remove(item.id)">
          <X class="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  </Teleport>
</template>
