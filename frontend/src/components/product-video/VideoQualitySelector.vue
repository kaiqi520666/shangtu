<script setup>
import AppOptionCards from "@/components/ui/AppOptionCards.vue";
import { videoResolutionOptions } from "@/constants/product-video.js";

defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  options: {
    type: Array,
    default: () => videoResolutionOptions,
  },
});

const emit = defineEmits(["update:modelValue"]);
</script>

<template>
  <div>
    <label class="mb-1.5 block text-xs font-bold text-slate-500">视频清晰度</label>
    <AppOptionCards
      :model-value="modelValue"
      :options="options.map((option) => ({ value: option.value, label: option.label, description: option.subtitle }))"
      align="center"
      @update:model-value="emit('update:modelValue', $event)"
    />
  </div>
</template>
