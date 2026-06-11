<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    required: true,
  },
  slides: {
    type: Array,
    required: true,
  },
  activeIndex: {
    type: Number,
    default: 0,
  },
})

const activeSlide = computed(() => props.slides[props.activeIndex] || props.slides[0])
</script>

<template>
  <div class="flex min-h-full flex-col items-center justify-center px-8 py-12 text-center">
    <h1 class="text-2xl font-black tracking-normal text-slate-950">{{ title }}</h1>
    <p class="mt-3 text-sm font-medium text-slate-500">{{ subtitle }}</p>

    <div v-if="activeSlide" class="mt-12 w-full max-w-3xl rounded-3xl bg-white p-6 text-left shadow-sm">
      <p class="mb-4 text-sm font-bold text-slate-800">{{ activeSlide.caption }}</p>
      <div class="flex items-stretch gap-3">
        <div class="flex w-32 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-slate-100">
          <img :src="activeSlide.sourceImage" class="h-full w-full object-cover" alt="参考图" />
        </div>
        <div class="flex w-10 shrink-0 items-center justify-center text-primary">
          <span class="h-1.5 w-8 rounded-full bg-primary/20"></span>
        </div>
        <div class="grid min-w-0 flex-1 grid-cols-3 gap-2">
          <div
            v-for="image in activeSlide.resultImages"
            :key="image"
            class="aspect-[3/4] overflow-hidden rounded-xl bg-slate-100"
          >
            <img :src="image" class="h-full w-full object-cover" alt="生成示例" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="slides.length > 1" class="mt-4 flex items-center gap-2">
      <span
        v-for="(_, index) in slides"
        :key="index"
        class="h-1.5 w-1.5 rounded-full"
        :class="index === activeIndex ? 'bg-slate-900' : 'bg-slate-300'"
      ></span>
    </div>
  </div>
</template>
