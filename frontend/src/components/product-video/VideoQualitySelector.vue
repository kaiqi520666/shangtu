<script setup>
import { videoResolutionOptions } from "@/constants/productVideo.js";

defineProps({
  modelValue: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue"]);
</script>

<template>
  <div>
    <label class="mb-1.5 block text-xs font-bold text-slate-500">视频清晰度</label>
    <div class="grid grid-cols-3 gap-2">
      <button
        v-for="option in videoResolutionOptions"
        :key="option.value"
        type="button"
        class="rounded-lg border px-3 py-2 text-center transition-all"
        :class="
          modelValue === option.value
            ? 'border-primary bg-primary/10 text-primary shadow-sm'
            : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50'
        "
        @click="emit('update:modelValue', option.value)"
      >
        <span class="block text-sm font-bold leading-tight">{{ option.label }}</span>
        <span class="mt-0.5 block text-xs leading-tight" :class="modelValue === option.value ? 'text-primary' : 'text-slate-400'">
          {{ option.subtitle }}
        </span>
      </button>
    </div>
  </div>
</template>
