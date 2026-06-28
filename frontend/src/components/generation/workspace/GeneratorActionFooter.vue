<script setup>
defineProps({
  primaryText: {
    type: String,
    required: true,
  },
  primaryDisabled: {
    type: Boolean,
    default: false,
  },
  secondaryText: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['primary', 'secondary'])
</script>

<template>
  <div class="shrink-0 border-t border-slate-200 bg-white/95 p-4 shadow-[0_-4px_12px_rgba(0,0,0,0.02)] backdrop-blur-sm">
    <div class="flex gap-2.5">
      <button
        v-if="secondaryText"
        type="button"
        class="min-w-28 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold text-slate-700 transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
        @click="emit('secondary')"
      >
        {{ secondaryText }}
      </button>
      <button
        type="button"
        :disabled="primaryDisabled"
        class="relative flex flex-1 items-center justify-center gap-2 overflow-hidden rounded-xl px-4 py-3 text-xs font-bold shadow-md transition-all duration-300"
        :class="
          primaryDisabled
            ? 'cursor-not-allowed border border-slate-200 bg-slate-100 text-slate-400'
            : 'bg-primary text-white shadow-primary/20 hover:-translate-y-0.5 hover:bg-secondary'
        "
        @click="emit('primary')"
      >
        <slot name="primary-icon" />
        <span>{{ primaryText }}</span>
      </button>
    </div>
  </div>
</template>
