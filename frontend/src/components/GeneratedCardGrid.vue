<script setup>
import { Check, Download, LoaderCircle, Maximize2, Pencil, TriangleAlert } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast.js'

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

const emit = defineEmits(['toggle-card', 'download-card', 'edit-card', 'zoom-card'])

const toast = useToast()

function isFailed(card) {
  return card.status === 'failed' || card.status === 'timeout'
}

function isRegenerating(card) {
  return (card.status === 'processing' || card.status === 'pending') && card.dataUrl
}

function shortFailReason(card) {
  if (card.errorMessage) return card.errorMessage
  return card.status === 'timeout' ? '生成超时，请稍后重试' : '生成失败，请稍后重试'
}

function handleDownload(card) {
  if (isFailed(card)) {
    toast.info('该图片生成失败，无法下载')
    return
  }
  emit('download-card', card)
}
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
          v-if="card.status === 'done' && card.dataUrl"
          type="button"
          class="rounded-lg border border-slate-200 bg-white/95 p-1.5 text-slate-600 shadow transition-colors hover:bg-white hover:text-primary"
          title="编辑图片"
          @click="emit('edit-card', card)"
        >
          <Pencil class="h-3.5 w-3.5" />
        </button>
        <button
          v-if="card.status === undefined || (card.status === 'done' && card.dataUrl)"
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
        <img v-if="card.dataUrl" :src="card.dataUrl" referrerpolicy="no-referrer" class="max-h-full max-w-full object-contain drop-shadow-md transition-transform duration-300 group-hover:scale-[1.03]" alt="AI主图" />
        <div v-else-if="isFailed(card)" class="flex flex-col items-center gap-1.5 px-4 text-center text-rose-500">
          <TriangleAlert class="h-7 w-7" />
          <span class="text-xs font-semibold">生成失败</span>
          <span
            v-if="card.errorMessage"
            class="line-clamp-2 text-[11px] font-medium leading-snug text-rose-400"
            :title="card.errorMessage"
          >
            {{ card.errorMessage }}
          </span>
        </div>
        <div v-else class="flex flex-col items-center gap-2 text-primary">
          <LoaderCircle class="h-7 w-7 animate-spin" />
          <span class="text-xs font-semibold text-slate-500">
            {{ card.status === 'processing' ? '生成中...' : '排队中...' }}
          </span>
        </div>
        <!-- 重新生成遮罩：有旧图 + 正在生成 -->
        <div v-if="isRegenerating(card)" class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/70 backdrop-blur-[2px]">
          <LoaderCircle class="h-7 w-7 animate-spin text-primary" />
          <span class="text-xs font-semibold text-slate-600">重新生成中...</span>
        </div>
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
          <div v-if="isFailed(card)" class="mt-1.5 space-y-0.5">
            <p class="line-clamp-2 text-[11px] font-medium leading-snug text-rose-500" :title="shortFailReason(card)">
              原因：{{ shortFailReason(card) }}
            </p>
            <p class="text-[11px] font-medium text-emerald-600">本次失败未消耗额度</p>
          </div>
        </div>
        <div class="flex items-center justify-between border-t border-slate-100 pt-2">
          <span class="text-xs font-medium text-slate-400">适配：{{ platform }} / {{ language }}</span>
          <button
            v-if="card.status === undefined || (card.status === 'done' && card.dataUrl)"
            type="button"
            class="flex items-center gap-1 text-xs font-bold text-primary hover:text-secondary"
            @click="handleDownload(card)"
          >
            下载单张
            <Download class="h-3 w-3" />
          </button>
          <button
            v-else-if="isFailed(card)"
            type="button"
            class="flex cursor-not-allowed items-center gap-1 text-xs font-semibold text-slate-300"
            @click.stop="handleDownload(card)"
          >
            下载单张
            <Download class="h-3 w-3" />
          </button>
          <span v-else class="text-xs font-medium text-slate-400">
            {{ card.status === 'processing' ? '生成中...' : '排队中...' }}
          </span>
        </div>
      </div>
    </article>
  </div>
</template>
