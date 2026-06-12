<script setup>
import { useConfirm } from '@/composables/useConfirm.js'

const { state, confirm, cancel } = useConfirm()

function onKeydown(e) {
  if (e.key === 'Escape') cancel()
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="state.open"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/60 p-6 backdrop-blur-sm"
        @click="cancel"
        @keydown="onKeydown"
      >
        <div
          class="w-full max-w-sm overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
          @click.stop
        >
          <div class="px-6 pt-6 pb-2">
            <h3 class="text-sm font-bold text-slate-800">{{ state.title }}</h3>
            <p v-if="state.message" class="mt-2 text-xs leading-relaxed text-slate-600">{{ state.message }}</p>
          </div>
          <div class="flex items-center justify-end gap-2.5 px-6 pb-5 pt-4">
            <button
              type="button"
              class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50"
              @click="cancel"
            >
              {{ state.cancelText }}
            </button>
            <button
              type="button"
              class="rounded-lg px-4 py-2 text-xs font-bold text-white shadow-sm transition-colors"
              :class="state.tone === 'danger'
                ? 'bg-rose-500 hover:bg-rose-600'
                : 'bg-primary hover:bg-secondary'"
              @click="confirm"
            >
              {{ state.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
