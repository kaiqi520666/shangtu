<script setup>
import { AudioLines } from "lucide-vue-next";
import GeneratedMediaCard from "./GeneratedMediaCard.vue";

defineProps({ cards: { type: Array, required: true }, downloading: { type: Boolean, default: false } });
const emit = defineEmits(["toggle-card", "download-card", "delete-card"]);
</script>

<template>
  <div class="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
    <GeneratedMediaCard v-for="card in cards" :key="card.id" :card="card" :label="card.strategyTitle || 'AI配音'" :meta-text="`${card.settingsSnapshot?.voice_name || ''} · MP3 / 24kHz`" media-label="音频" aspect-class="aspect-[4/3]" :downloading="downloading" @toggle="emit('toggle-card', $event)" @download="emit('download-card', $event)" @delete="emit('delete-card', $event)">
      <template #preview="{ card: item }"><div class="flex h-full w-full flex-col items-center justify-center gap-4 bg-slate-50 p-5"><AudioLines class="h-10 w-10 text-primary" /><audio :src="item.dataUrl" controls preload="metadata" class="w-full" @click.stop @keyup.stop></audio></div></template>
    </GeneratedMediaCard>
  </div>
</template>
