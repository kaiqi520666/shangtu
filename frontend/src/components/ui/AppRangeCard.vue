<script setup>
import { computed } from "vue";

const props = defineProps({
  modelValue: {
    type: [Number, String],
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  hint: {
    type: String,
    default: "",
  },
  min: {
    type: Number,
    required: true,
  },
  max: {
    type: Number,
    required: true,
  },
  step: {
    type: Number,
    default: 1,
  },
  minLabel: {
    type: String,
    default: "",
  },
  midLabel: {
    type: String,
    default: "",
  },
  maxLabel: {
    type: String,
    default: "",
  },
  valueFormatter: {
    type: Function,
    default: (value) => String(value),
  },
});

const emit = defineEmits(["update:modelValue"]);

const progressPercent = computed(() => {
  const current = Number(props.modelValue);
  return ((current - props.min) / (props.max - props.min)) * 100;
});

function updateValue(event) {
  emit("update:modelValue", Number(event.target.value));
}
</script>

<template>
  <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold text-slate-800">{{ props.title }}</p>
        <p v-if="props.hint" class="mt-1 text-[11px] leading-5 text-slate-400">{{ props.hint }}</p>
      </div>
      <span class="rounded-full bg-white px-3 py-1 text-sm font-black text-slate-900 shadow-sm">
        {{ props.valueFormatter(props.modelValue) }}
      </span>
    </div>

    <div class="mt-4">
      <div class="relative">
        <div class="absolute inset-x-2 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-slate-200"></div>
        <div
          class="absolute left-2 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-primary"
          :style="{ width: `calc((100% - 16px) * ${progressPercent / 100})` }"
        ></div>
        <span
          class="pointer-events-none absolute top-1/2 z-10 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary"
          :style="{ left: `calc(8px + (100% - 16px) * ${progressPercent / 100})` }"
        ></span>
        <input
          :value="props.modelValue"
          type="range"
          :min="props.min"
          :max="props.max"
          :step="props.step"
          class="app-range-input relative h-6 w-full cursor-pointer appearance-none bg-transparent"
          @input="updateValue"
        />
      </div>
      <div class="mt-2 flex items-center justify-between text-[11px] text-slate-400">
        <span>{{ props.minLabel }}</span>
        <span v-if="props.midLabel">{{ props.midLabel }}</span>
        <span>{{ props.maxLabel }}</span>
      </div>
    </div>

    <div v-if="$slots.footer" class="mt-3">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<style scoped>
.app-range-input::-webkit-slider-runnable-track {
  height: 6px;
  background: transparent;
}

.app-range-input::-webkit-slider-thumb {
  width: 16px;
  height: 16px;
  margin-top: -5px;
  -webkit-appearance: none;
  appearance: none;
  border: 0;
  border-radius: 9999px;
  background: transparent;
  opacity: 0;
}

.app-range-input::-moz-range-track {
  height: 6px;
  background: transparent;
}

.app-range-input::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border: 0;
  border-radius: 9999px;
  background: transparent;
  opacity: 0;
}
</style>
