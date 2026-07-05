<script setup>
const props = defineProps({
  modelValue: {
    type: [String, Number],
    required: true,
  },
  options: {
    type: Array,
    required: true,
  },
  columns: {
    type: Number,
    default: 2,
  },
  align: {
    type: String,
    default: "left",
  },
});

const emit = defineEmits(["update:modelValue"]);
</script>

<template>
  <div class="grid gap-3" :style="{ gridTemplateColumns: `repeat(${props.columns}, minmax(0, 1fr))` }">
    <button
      v-for="option in props.options"
      :key="option.value"
      type="button"
      class="rounded-xl border px-3 py-3 transition-all"
      :class="
        props.modelValue === option.value
          ? 'border-primary bg-primary/8 text-primary shadow-sm'
          : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
      "
      @click="emit('update:modelValue', option.value)"
    >
      <span class="block text-sm font-black" :class="props.align === 'center' ? 'text-center' : 'text-left'">
        {{ option.label }}
      </span>
      <span
        v-if="option.description"
        class="mt-1 block text-xs"
        :class="[props.modelValue === option.value ? 'text-primary/80' : 'text-slate-400', props.align === 'center' ? 'text-center' : 'text-left']"
      >
        {{ option.description }}
      </span>
    </button>
  </div>
</template>
