<script setup>
import { ref } from "vue";
import { Play, Volume2 } from "lucide-vue-next";
import { videoDemoTypes } from "@/constants/productVideo.js";

const playingType = ref("");

function togglePlay(typeId) {
  playingType.value = playingType.value === typeId ? "" : typeId;
}
</script>

<template>
  <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
    <article
      v-for="item in videoDemoTypes"
      :key="item.typeId"
      class="group cursor-pointer"
      @click="togglePlay(item.typeId)"
    >
      <div
        class="relative aspect-[9/16] overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 shadow-sm transition-all group-hover:-translate-y-1 group-hover:shadow-md"
      >
        <video
          v-if="playingType === item.typeId"
          :src="item.videoUrl"
          :poster="item.posterUrl"
          class="h-full w-full object-cover"
          autoplay
          loop
          playsinline
          controls
          @click.stop
        ></video>
        <img v-else :src="item.posterUrl" class="h-full w-full object-cover" :alt="item.title" />

        <button
          type="button"
          class="absolute bottom-3 left-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-slate-900 shadow-lg backdrop-blur transition-transform hover:scale-105"
          @click.stop="togglePlay(item.typeId)"
        >
          <Play v-if="playingType !== item.typeId" class="h-4 w-4 fill-current" />
          <Volume2 v-else class="h-4 w-4" />
        </button>
      </div>
      <div class="mt-3 text-center">
        <h3 class="text-base font-black text-slate-900">{{ item.title }}</h3>
        <p class="mt-1 text-xs font-semibold text-slate-400">{{ item.subtitle }}</p>
      </div>
    </article>
  </div>
</template>
