<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Check, ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  options: {
    type: Array,
    required: true,
  },
  placeholder: {
    type: String,
    default: '请选择',
  },
})

const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const root = ref(null)

const selectedLabel = computed(() => {
  return props.options.find((option) => option.value === props.modelValue)?.label || props.placeholder
})

function selectOption(option) {
  emit('update:modelValue', option.value)
  open.value = false
}

function handleClickOutside(event) {
  if (root.value && !root.value.contains(event.target)) {
    open.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-left text-xs font-medium text-slate-800 transition-colors hover:border-primary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
      @click.stop="open = !open"
    >
      <span class="truncate">{{ selectedLabel }}</span>
      <ChevronDown class="ml-2 h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform" :class="open ? 'rotate-180 text-primary' : ''" />
    </button>

    <div
      v-if="open"
      class="absolute left-0 right-0 top-full z-40 mt-1 max-h-64 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg"
    >
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="flex w-full items-center justify-between gap-3 px-2.5 py-2 text-left text-xs font-medium transition-colors hover:bg-primary/10"
        :class="option.value === modelValue ? 'bg-primary/10 text-primary' : 'text-slate-700'"
        @click="selectOption(option)"
      >
        <span class="flex min-w-0 items-center gap-2">
          <span class="shrink-0">{{ option.label }}</span>
          <span v-if="option.description" class="truncate text-slate-400">{{ option.description }}</span>
        </span>
        <Check v-if="option.value === modelValue" class="h-3.5 w-3.5" />
      </button>
    </div>
  </div>
</template>
