<script setup>
import { Download, Trash2 } from 'lucide-vue-next'
import AppCheckbox from '@/components/ui/AppCheckbox.vue'

defineProps({
  cards: {
    type: Array,
    required: true,
  },
  scenarioLabel: {
    type: Function,
    default: () => '',
  },
})

const emit = defineEmits(['toggle-card', 'download-card', 'zoom-card', 'delete-card'])

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<template>
  <div class="grid grid-cols-2 gap-5 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
    <article
      v-for="card in cards"
      :key="card.id"
      class="group relative flex flex-col justify-between overflow-hidden rounded-2xl border bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md"
      :class="card.selected ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'"
    >
      <!-- 左上：勾选 + 场景标签 -->
      <div class="absolute left-2.5 top-2.5 z-10 flex items-center gap-2">
        <AppCheckbox
          :model-value="card.selected"
          @change="emit('toggle-card', card.id)"
        />
        <span v-if="scenarioLabel(card)" class="rounded-full border border-slate-200 bg-white/90 px-2 py-0.5 text-xs font-bold text-slate-700 shadow-sm backdrop-blur-sm">
          {{ scenarioLabel(card) }}
        </span>
      </div>

      <!-- 右上：hover 操作 -->
      <div class="absolute right-2.5 top-2.5 z-10 flex gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          type="button"
          class="rounded-lg border border-slate-200 bg-white/95 p-1.5 text-slate-600 shadow transition-colors hover:bg-white hover:text-rose-500"
          title="删除图片"
          @click="emit('delete-card', card)"
        >
          <Trash2 class="h-3.5 w-3.5" />
        </button>
      </div>

      <!-- 图片区域 -->
      <button
        type="button"
        class="relative flex aspect-square cursor-pointer items-center justify-center overflow-hidden bg-slate-100 p-3"
        @click="emit('zoom-card', card)"
      >
        <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/[0.01]"></div>
        <img
          v-if="card.dataUrl"
          :src="card.dataUrl"
          referrerpolicy="no-referrer"
          class="max-h-full max-w-full object-contain drop-shadow-md transition-transform duration-300 group-hover:scale-[1.03]"
          alt="资产图片"
        />
      </button>

      <!-- 底部信息 -->
      <div class="flex items-center justify-between border-t border-slate-100 bg-white p-3">
        <span class="truncate text-xs font-medium text-slate-500">
          {{ formatDate(card.createdAt) }}
        </span>
        <button
          type="button"
          class="ml-2 flex shrink-0 items-center gap-1 text-xs font-bold text-primary hover:text-secondary"
          @click="emit('download-card', card)"
        >
          下载
          <Download class="h-3 w-3" />
        </button>
      </div>
    </article>
  </div>
</template>
