<script setup>
import { computed } from "vue";
import AppRangeCard from "@/components/ui/AppRangeCard.vue";
import { getVideoCreditCost } from "@/constants/product-video.js";

const props = defineProps({
  duration: {
    type: Number,
    required: true,
  },
  resolution: {
    type: String,
    required: true,
  },
  creditCosts: {
    type: Object,
    required: true,
  },
});

const creditCost = computed(() =>
  getVideoCreditCost({
    duration: props.duration,
    resolution: props.resolution,
    costs: props.creditCosts,
  }),
);

const emit = defineEmits(["update:duration"]);

function formatDuration(value) {
  return `${value} 秒`;
}
</script>

<template>
  <AppRangeCard
    :model-value="duration"
    title="视频时长"
    hint="3-15 秒，可拖动调整"
    :min="3"
    :max="15"
    :step="1"
    min-label="3 秒"
    max-label="15 秒"
    :value-formatter="formatDuration"
    @update:model-value="emit('update:duration', $event)"
  >
    <template #footer>
      <p class="rounded-lg bg-white px-3 py-2 text-xs font-semibold text-slate-600">
        预计消耗：
        <span class="font-black text-primary">{{ resolution }} × {{ duration }}秒 = {{ creditCost || "-" }} 积分</span>
      </p>
    </template>
  </AppRangeCard>
</template>
