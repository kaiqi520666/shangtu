<script setup>
import { Check } from 'lucide-vue-next'
import AppSelect from '@/components/ui/AppSelect.vue'
import { outfitAngleOptions, outfitFrameOptions } from '@/constants/outfit.js'

defineProps({
  pose: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    required: true,
  },
})

const emit = defineEmits(['toggle', 'update'])
</script>

<template>
  <article class="rounded-2xl bg-slate-50 p-3">
    <div class="flex items-start gap-2.5">
      <button
        type="button"
        class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border"
        :class="pose.selected ? 'border-primary bg-primary text-white' : 'border-slate-300 bg-white text-transparent'"
        @click="emit('toggle', index)"
      >
        <Check class="h-3 w-3 stroke-[3]" />
      </button>
      <div class="min-w-0 flex-1">
        <div class="mb-1 flex items-center justify-between gap-2">
          <span class="text-xs font-bold text-slate-900">{{ pose.sceneName }}</span>
          <span class="text-xs font-semibold text-primary">方案 {{ index + 1 }}</span>
        </div>
        <p class="text-xs leading-relaxed text-slate-500">{{ pose.text }}</p>
      </div>
    </div>

    <div class="mt-3 grid grid-cols-2 gap-2">
      <AppSelect
        :model-value="pose.frame"
        :options="outfitFrameOptions"
        @update:model-value="emit('update', index, { frame: $event })"
      />
      <AppSelect
        :model-value="pose.angle"
        :options="outfitAngleOptions"
        @update:model-value="emit('update', index, { angle: $event })"
      />
    </div>
  </article>
</template>
