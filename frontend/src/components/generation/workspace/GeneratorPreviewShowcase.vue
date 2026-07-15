<script setup>
import { computed, ref } from 'vue'
import { Play, Square } from 'lucide-vue-next'

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
  imageUrl: {
    type: String,
    default: '',
  },
  imageAlt: {
    type: String,
    default: '',
  },
  activeIndex: {
    type: Number,
    default: 0,
  },
  mediaType: {
    type: String,
    default: 'image',
  },
})

const activeSlide = computed(() => props.slides[props.activeIndex] || props.slides[0])
const playingSlideKey = ref('')

function getSlideKey(slide, index) {
  return String(slide.id || slide.typeId || slide.videoUrl || index)
}

function toggleVideo(slide, index) {
  const key = getSlideKey(slide, index)
  playingSlideKey.value = playingSlideKey.value === key ? '' : key
}
</script>

<template>
  <div class="flex min-h-full flex-col items-center justify-center px-6 py-10 text-center">
    <template v-if="!imageUrl">
      <h1 class="text-xl font-bold tracking-normal text-slate-950">{{ title }}</h1>
      <p class="mt-2 text-sm font-medium text-slate-500">{{ subtitle }}</p>
    </template>

    <div v-if="imageUrl" class="w-full max-w-3xl overflow-hidden rounded-lg bg-slate-100">
      <img :src="imageUrl" :alt="imageAlt" class="aspect-[16/9] w-full object-cover" />
    </div>

    <div
      v-else-if="mediaType === 'video' && slides.length > 0"
      class="mt-8 grid w-full max-w-6xl gap-4 md:grid-cols-2 xl:grid-cols-4"
    >
      <article
        v-for="(slide, index) in slides"
        :key="getSlideKey(slide, index)"
        class="group cursor-pointer"
        @click="toggleVideo(slide, index)"
      >
        <div class="relative aspect-[9/16] overflow-hidden rounded-lg border border-slate-200 bg-slate-100 shadow-sm">
          <video
            v-if="playingSlideKey === getSlideKey(slide, index)"
            :src="slide.videoUrl"
            :poster="slide.posterUrl"
            class="h-full w-full object-cover"
            autoplay
            loop
            playsinline
            controls
            @click.stop
          ></video>
          <img v-else :src="slide.posterUrl" class="h-full w-full object-cover" :alt="slide.title" />

          <button
            type="button"
            class="absolute bottom-3 left-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-slate-900 shadow-lg backdrop-blur transition-transform hover:scale-105"
            :title="playingSlideKey === getSlideKey(slide, index) ? '停止预览' : '播放预览'"
            @click.stop="toggleVideo(slide, index)"
          >
            <Play v-if="playingSlideKey !== getSlideKey(slide, index)" class="h-4 w-4 fill-current" />
            <Square v-else class="h-4 w-4 fill-current" />
          </button>
        </div>
        <div class="mt-3 text-center">
          <h3 class="text-base font-black text-slate-900">{{ slide.title }}</h3>
          <p class="mt-1 text-xs font-semibold text-slate-400">{{ slide.subtitle }}</p>
        </div>
      </article>
    </div>

    <div v-else-if="activeSlide" class="mt-8 w-full max-w-3xl rounded-lg bg-white p-5 text-left shadow-sm">
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

    <div v-if="mediaType === 'image' && slides.length > 1" class="mt-4 flex items-center gap-2">
      <span
        v-for="(_, index) in slides"
        :key="index"
        class="h-1.5 w-1.5 rounded-full"
        :class="index === activeIndex ? 'bg-slate-900' : 'bg-slate-300'"
      ></span>
    </div>
  </div>
</template>
