<script setup>
import { computed } from "vue";
import AppRangeCard from "@/components/ui/AppRangeCard.vue";
import { getVideoCreditCost, videoDurationOptions } from "@/constants/product-video.js";

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

const durationIndex = computed(() => {
  const index = videoDurationOptions.indexOf(Number(props.duration));
  return index >= 0 ? index : videoDurationOptions.indexOf(8);
});

function formatDuration(value) {
  return `${videoDurationOptions[value] || 8} 秒`;
}

function updateDuration(index) {
  emit("update:duration", videoDurationOptions[index] || 8);
}
</script>

<template>
  <AppRangeCard
    :model-value="durationIndex"
    title="视频时长"
    hint="4 / 8 / 10 / 12 / 15 秒，可拖动调整"
    :min="0"
    :max="videoDurationOptions.length - 1"
    :step="1"
    min-label="4 秒"
    mid-label="10 秒"
    max-label="15 秒"
    :value-formatter="formatDuration"
    @update:model-value="updateDuration"
  >
    <template #footer>
      <p class="rounded-lg bg-white px-3 py-2 text-xs font-semibold text-slate-600">
        预计消耗：
        <span class="font-black text-primary">{{ resolution }} × {{ duration }}秒 = {{ creditCost || "-" }} 积分</span>
      </p>
    </template>
  </AppRangeCard>
</template>
