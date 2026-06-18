<script setup>
import { Download, LoaderCircle, Play, Square, Trash2, TriangleAlert } from 'lucide-vue-next'
import { ref } from 'vue'
import AppCheckbox from '@/components/ui/AppCheckbox.vue'
import { useToast } from '@/composables/useToast.js'
import { getSnapshotScene, getSnapshotValue } from '@/utils/generationSnapshots.js'

defineProps({
  cards: {
    type: Array,
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
  videoLabel: {
    type: String,
    required: true,
  },
  getModuleName: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['toggle-card', 'download-card', 'zoom-card', 'delete-card'])

const toast = useToast()
const playingCardId = ref('')

function isFailed(card) {
  return card.status === 'failed' || card.status === 'timeout'
}

function shortFailReason(card) {
  if (card.errorMessage) return card.errorMessage
  return card.status === 'timeout' ? '生成超时，请稍后重试' : '生成失败，请稍后重试'
}

function canDownload(card) {
  return card.status === 'done' && Boolean(card.dataUrl)
}

function handleDownload(card) {
  if (isFailed(card)) {
    toast.info('该视频生成失败，无法下载')
    return
  }
  emit('download-card', card)
}

function togglePlay(card) {
  if (!canDownload(card)) return
  playingCardId.value = playingCardId.value === card.id ? '' : card.id
}

function getCardMetaText(card, fallbackPlatform, fallbackLanguage, fallbackVideoLabel) {
  const snapshot = card.settingsSnapshot || {}
  const scene = getSnapshotScene(snapshot)
  const platformText =
    scene.marketLabel ||
    snapshot.market_label ||
    getSnapshotValue(snapshot, 'platform') ||
    scene.market ||
    snapshot.market ||
    fallbackPlatform
  const languageText = scene.languageLabel || snapshot.language_label || getSnapshotValue(snapshot, 'language') || fallbackLanguage
  const duration = scene.duration ?? snapshot.duration
  const resolution = scene.resolution || snapshot.resolution || snapshot.quality
  const durationText = duration ? `${duration}秒` : ''
  const resolutionText = resolution || ''
  const videoText = [resolutionText, durationText].filter(Boolean).join(' / ') || fallbackVideoLabel
  return [platformText, languageText, videoText].filter(Boolean).join(' ')
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
        <AppCheckbox
          :model-value="card.selected"
          @change="emit('toggle-card', card.id)"
        />
        <span class="rounded-full border border-slate-200 bg-white/90 px-2 py-0.5 text-xs font-bold text-slate-700 shadow-sm backdrop-blur-sm">
          {{ getModuleName(card.typeId) }}
        </span>
      </div>

      <div class="absolute right-2.5 top-2.5 z-10 flex gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          v-if="card.status !== 'pending' && card.status !== 'processing'"
          type="button"
          class="rounded-lg border border-slate-200 bg-white/95 p-1.5 text-slate-600 shadow transition-colors hover:bg-white hover:text-rose-500"
          title="删除视频"
          @click="emit('delete-card', card)"
        >
          <Trash2 class="h-3.5 w-3.5" />
        </button>
      </div>

      <div
        role="button"
        tabindex="0"
        class="relative flex aspect-[9/16] cursor-pointer items-center justify-center overflow-hidden bg-slate-100"
        @click="canDownload(card) ? togglePlay(card) : undefined"
        @keyup.enter="canDownload(card) ? togglePlay(card) : undefined"
      >
        <video
          v-if="card.dataUrl && playingCardId === card.id"
          :src="card.dataUrl"
          class="h-full w-full object-cover"
          autoplay
          loop
          playsinline
          controls
          @click.stop
        ></video>
        <video
          v-else-if="card.dataUrl"
          :src="card.dataUrl"
          class="h-full w-full object-cover"
          muted
          playsinline
          preload="metadata"
        ></video>
        <div v-if="canDownload(card)" class="absolute bottom-3 left-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-slate-900 shadow-lg backdrop-blur">
          <Play v-if="playingCardId !== card.id" class="h-4 w-4 fill-current" />
          <Square v-else class="h-4 w-4 fill-current" />
        </div>
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
      </div>

      <div class="flex flex-1 flex-col justify-between border-t border-slate-100 bg-white p-3">
        <div v-if="isFailed(card)" class="mb-1.5 space-y-0.5">
          <p class="line-clamp-2 text-[11px] font-medium leading-snug text-rose-500" :title="shortFailReason(card)">
            原因：{{ shortFailReason(card) }}
          </p>
          <p class="text-[11px] font-medium text-emerald-600">本次失败未消耗额度</p>
        </div>
        <div class="flex items-center justify-between gap-2">
          <span class="min-w-0 truncate text-xs font-medium text-slate-500">
            {{ getCardMetaText(card, platform, language, videoLabel) }}
          </span>
          <button
            v-if="card.status !== 'pending' && card.status !== 'processing'"
            type="button"
            class="flex shrink-0 items-center gap-1 text-xs"
            :class="canDownload(card) ? 'font-bold text-primary hover:text-secondary' : 'cursor-not-allowed font-semibold text-slate-300'"
            @click.stop="handleDownload(card)"
          >
            下载视频
            <Download class="h-3 w-3" />
          </button>
          <span v-else class="shrink-0 text-xs font-medium text-slate-400">
            {{ card.status === 'processing' ? '生成中...' : '排队中...' }}
          </span>
        </div>
      </div>
    </article>
  </div>
</template>
