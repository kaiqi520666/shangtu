<script setup>
import { computed } from "vue";
import { getVideoCreditCost } from "@/constants/productVideo.js";

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

const emit = defineEmits(["update:duration"]);

const creditCost = computed(() =>
  getVideoCreditCost({
    duration: props.duration,
    resolution: props.resolution,
    costs: props.creditCosts,
  }),
);

function updateDuration(event) {
  emit("update:duration", Number(event.target.value));
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs font-bold text-slate-700">视频时长</p>
        <p class="mt-0.5 text-xs text-slate-400">3-15 秒，可拖动调整</p>
      </div>
      <span class="rounded-full bg-white px-3 py-1 text-sm font-black text-slate-900 shadow-sm">{{ duration }} 秒</span>
    </div>
    <input
      :value="duration"
      type="range"
      min="3"
      max="15"
      step="1"
      class="mt-4 h-2 w-full cursor-pointer accent-primary"
      @input="updateDuration"
    />
    <div class="mt-2 flex justify-between text-xs text-slate-400">
      <span>3 秒</span>
      <span>15 秒</span>
    </div>
    <p class="mt-3 rounded-lg bg-white px-3 py-2 text-xs font-semibold text-slate-600">
      预计消耗：
      <span class="font-black text-primary">{{ resolution }} × {{ duration }}秒 = {{ creditCost || "-" }} 积分</span>
    </p>
  </div>
</template>
