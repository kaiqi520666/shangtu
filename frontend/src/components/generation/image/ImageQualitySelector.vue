<script setup>
import { computed } from "vue";
import AppOptionCards from "@/components/ui/AppOptionCards.vue";
import { isQualitySupported, qualityOptions } from "@/constants/generator.js";

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  ratio: {
    type: String,
    required: true,
  },
  outputLabel: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue"]);

const options = computed(() =>
  qualityOptions.map((quality) => {
    const disabled = !isQualitySupported(props.ratio, quality.value);
    return {
      value: quality.value,
      label: quality.title,
      description: disabled ? "不支持" : quality.subtitle,
      disabled,
    };
  }),
);

function selectQuality(quality) {
  if (!isQualitySupported(props.ratio, quality)) return;
  emit("update:modelValue", quality);
}
</script>

<template>
  <div>
    <label class="mb-1.5 block text-xs font-bold text-slate-500">图片质量</label>
    <AppOptionCards
      :model-value="modelValue"
      :options="options"
      :columns="3"
      align="center"
      @update:model-value="selectQuality"
    />
    <p class="mt-2 text-xs text-slate-400">当前输出：{{ outputLabel }}</p>
  </div>
</template>
