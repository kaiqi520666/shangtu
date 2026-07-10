<script setup>
import { Play } from "lucide-vue-next";
import GeneratorPanelSection from "@/components/generation/workspace/GeneratorPanelSection.vue";
import { videoDemoTypes } from "@/constants/product-video.js";

defineProps({
  modelValue: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue"]);
</script>

<template>
  <GeneratorPanelSection title="选择视频方向" description="选方向后，系统会自动切换需要上传的素材类型。">
    <div class="grid grid-cols-2 gap-2.5">
      <button
        v-for="item in videoDemoTypes"
        :key="item.typeId"
        type="button"
        class="group rounded-xl border p-3 text-left transition-all"
        :class="
          modelValue === item.typeId
            ? 'border-primary bg-primary/5 shadow-sm'
            : 'border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white'
        "
        @click="emit('update:modelValue', item.typeId)"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="text-sm font-black text-slate-900">{{ item.title }}</span>
          <span
            class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
            :class="modelValue === item.typeId ? 'bg-primary text-white' : 'bg-white text-slate-400 group-hover:text-primary'"
          >
            <Play class="h-3 w-3 fill-current" />
          </span>
        </div>
        <p class="mt-1 line-clamp-1 text-xs text-slate-400">{{ item.subtitle }}</p>
      </button>
    </div>
  </GeneratorPanelSection>
</template>
