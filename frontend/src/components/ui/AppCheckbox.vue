<script setup>
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: "",
  },
  size: {
    type: String,
    default: "md",
    validator: (value) => ["sm", "md"].includes(value),
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const boxClass = computed(() => (props.size === 'sm' ? 'h-3.5 w-3.5 rounded' : 'h-5 w-5 rounded-md'))
const iconClass = computed(() => (props.size === 'sm' ? 'h-2.5 w-2.5' : 'h-3 w-3'))

function handleChange(event) {
  if (props.disabled) return
  const nextValue = event.target.checked
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}
</script>

<template>
  <label
    class="inline-flex shrink-0 items-center gap-1.5 text-xs font-bold transition-colors"
    :class="[
      label ? 'text-slate-600 hover:text-slate-800' : '',
      disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
    ]"
    @click.stop
  >
    <input
      class="sr-only"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      @change="handleChange"
    />
    <span
      class="flex shrink-0 items-center justify-center border transition-colors"
      :class="[
        boxClass,
        modelValue
          ? 'border-primary bg-primary text-white'
          : 'border-slate-300 bg-white text-transparent hover:border-primary/40',
      ]"
    >
      <Check :class="[iconClass, 'stroke-[3]']" />
    </span>
    <span v-if="label">{{ label }}</span>
  </label>
</template>
