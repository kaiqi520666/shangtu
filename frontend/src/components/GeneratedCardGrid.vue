<script setup>
import { Check, Download, Maximize2, RefreshCw } from 'lucide-vue-next'

defineProps({
  cards: {
    type: Array,
    required: true,
  },
  ratio: {
    type: String,
    required: true,
  },
  platform: {
    type: String,
    required: true,
  },
  language: {
    type: String,
    required: true,
  },
  getModuleName: {
    type: Function,
    required: true,
  },
  getModuleStrategy: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['toggle-card', 'download-card', 'regenerate-card', 'zoom-card'])
</script>

<template>
  <div class="grid grid-cols-2 gap-5 md:grid-cols-3 xl:grid-cols-4">
    <article
      v-for="card in cards"
      :key="card.id"
      class="group relative flex flex-col justify-between overflow-hidden rounded-2xl border bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md"
      :class="card.selected ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'"
    >
      <div class="absolute left-2.5 top-2.5 z-10 flex items-center gap-2">
        <button
          type="button"
          class="flex h-5 w-5 items-center justify-center rounded-md border shadow-sm transition-all"
          :class="card.selected ? 'border-primary bg-primary text-white' : 'border-slate-300 bg-white/90 text-transparent backdrop-blur-sm hover:border-slate-400'"
          @click="emit('toggle-card', card.id)"
        >
          <Check class="h-3 w-3 stroke-[3]" />
        </button>
        <span class="rounded-full border border-slate-200 bg-white/90 px-2 py-0.5 text-xs font-bold text-slate-700 shadow-sm backdrop-blur-sm">
          {{ getModuleName(card.typeId) }}
        </span>
      </div>

      <div class="absolute right-2.5 top-2.5 z-10 flex gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          type="button"
          class="rounded-lg border border-slate-200 bg-white/95 p-1.5 text-slate-600 shadow transition-colors hover:bg-white hover:text-primary"
          title="重算该策略图"
          @click="emit('regenerate-card', card)"
        >
          <RefreshCw class="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          class="rounded-lg border border-slate-200 bg-white/95 p-1.5 text-slate-600 shadow transition-colors hover:bg-white hover:text-primary"
          title="放大预览"
          @click="emit('zoom-card', card)"
        >
          <Maximize2 class="h-3.5 w-3.5" />
        </button>
      </div>

      <button type="button" class="relative flex aspect-square cursor-pointer items-center justify-center overflow-hidden bg-slate-100 p-3" @click="emit('toggle-card', card.id)">
        <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/[0.01]"></div>
        <img :src="card.dataUrl" class="max-h-full max-w-full object-contain drop-shadow-md transition-transform duration-300 group-hover:scale-[1.03]" alt="AI主图" />
      </button>

      <div class="flex flex-1 flex-col justify-between space-y-1.5 border-t border-slate-100 bg-white p-3">
        <div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-800">{{ card.strategyTitle || getModuleName(card.typeId) }}</span>
            <span class="text-xs font-bold text-slate-400">{{ ratio }}</span>
          </div>
          <p class="mt-1 text-xs font-semibold leading-relaxed text-primary">
            策略解读：{{ card.strategyContent || getModuleStrategy(card.typeId) }}
          </p>
        </div>
        <div class="flex items-center justify-between border-t border-slate-100 pt-2">
          <span class="text-xs font-medium text-slate-400">适配：{{ platform }} / {{ language }}</span>
          <button type="button" class="flex items-center gap-1 text-xs font-bold text-primary hover:text-secondary" @click="emit('download-card', card)">
            下载单张
            <Download class="h-3 w-3" />
          </button>
        </div>
      </div>
    </article>
  </div>
</template>
