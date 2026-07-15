<script setup>
import { Play, Square } from "lucide-vue-next";
import { ref } from "vue";
import GeneratedMediaCard from "./GeneratedMediaCard.vue";
import { getSnapshotScene } from "@/utils/generationSnapshots.js";

const props = defineProps({
  cards: { type: Array, required: true },
  platform: { type: String, required: true },
  language: { type: String, required: true },
  videoLabel: { type: String, required: true },
  getModuleName: { type: Function, required: true },
  downloading: { type: Boolean, default: false },
});
const emit = defineEmits(["toggle-card", "download-card", "zoom-card", "delete-card"]);
const playingCardId = ref("");

function togglePlay(card) {
  playingCardId.value = playingCardId.value === card.id ? "" : card.id;
}

function metaText(card) {
  const snapshot = card.settingsSnapshot || {};
  const scene = getSnapshotScene(snapshot);
  const video = [scene.resolution || snapshot.quality, scene.duration ? `${scene.duration}秒` : ""].filter(Boolean).join(" / ") || props.videoLabel;
  return [scene.marketLabel || scene.market || snapshot.platform || props.platform, scene.languageLabel || scene.language || snapshot.language || props.language, video].filter(Boolean).join(" ");
}
</script>

<template>
  <div class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
    <GeneratedMediaCard v-for="card in cards" :key="card.id" :card="card" :label="getModuleName(card.typeId)" :meta-text="metaText(card)" media-label="视频" aspect-class="aspect-[9/16]" :downloading="downloading" @toggle="emit('toggle-card', $event)" @download="emit('download-card', $event)" @activate="togglePlay" @delete="emit('delete-card', $event)">
      <template #preview="{ card: item }">
        <video :src="item.dataUrl" class="h-full w-full object-cover" :muted="playingCardId !== item.id" :autoplay="playingCardId === item.id" :controls="playingCardId === item.id" playsinline preload="metadata" @click.stop></video>
        <div class="absolute bottom-3 left-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-slate-900 shadow-lg backdrop-blur"><Play v-if="playingCardId !== item.id" class="h-4 w-4 fill-current" /><Square v-else class="h-4 w-4 fill-current" /></div>
      </template>
    </GeneratedMediaCard>
  </div>
</template>
