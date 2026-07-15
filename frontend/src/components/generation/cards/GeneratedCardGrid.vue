<script setup>
import GeneratedMediaCard from "./GeneratedMediaCard.vue";
import { formatImageLabel } from "@/constants/generator.js";

const props = defineProps({
  cards: { type: Array, required: true },
  platform: { type: String, required: true },
  language: { type: String, required: true },
  imageLabel: { type: String, required: true },
  getModuleName: { type: Function, required: true },
  downloading: { type: Boolean, default: false },
});
const emit = defineEmits(["toggle-card", "download-card", "edit-card", "zoom-card", "delete-card"]);

function metaText(card) {
  const snapshot = card.settingsSnapshot || {};
  const image = snapshot.ratio || snapshot.quality
    ? formatImageLabel({ ratio: snapshot.ratio, quality: snapshot.quality })
    : props.imageLabel;
  return [snapshot.platform || props.platform, snapshot.language || props.language, image].filter(Boolean).join(" ");
}
</script>

<template>
  <div class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
    <GeneratedMediaCard v-for="card in cards" :key="card.id" :card="card" :label="getModuleName(card.typeId)" :meta-text="metaText(card)" media-label="图片" :downloading="downloading" editable @toggle="emit('toggle-card', $event)" @download="emit('download-card', $event)" @edit="emit('edit-card', $event)" @activate="emit('zoom-card', $event)" @delete="emit('delete-card', $event)">
      <template #preview="{ card: item }"><img :src="item.dataUrl" referrerpolicy="no-referrer" class="max-h-full max-w-full object-contain p-3 drop-shadow-md" alt="AI主图" /></template>
    </GeneratedMediaCard>
  </div>
</template>
