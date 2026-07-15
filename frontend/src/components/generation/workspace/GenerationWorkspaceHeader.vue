<script setup>
import { Clock3, Download, Plus, RefreshCw } from 'lucide-vue-next'

defineProps({
  title: { type: String, required: true },
  titleBadge: { type: String, required: true },
  hasCards: { type: Boolean, default: false },
  selectedCount: { type: Number, default: 0 },
  downloading: { type: Boolean, default: false },
  generating: { type: Boolean, default: false },
  mediaUnit: { type: String, required: true },
})
defineEmits(['update:title', 'select-all', 'download', 'create', 'history'])
</script>

<template>
  <div
    class="z-10 flex min-h-14 shrink-0 flex-wrap items-center gap-2 border-b border-slate-200 bg-white/90 px-4 py-2 sm:flex-nowrap sm:px-6"
  >
    <div class="flex min-w-0 flex-1 basis-full items-center gap-3 sm:basis-auto">
      <span
        class="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600"
        >{{ titleBadge }}</span
      >
      <input
        :value="title"
        type="text"
        class="min-w-0 flex-1 border-b border-transparent bg-transparent py-0.5 text-xs font-bold text-slate-800 hover:border-slate-300 focus:border-primary focus:outline-none sm:max-w-64"
        @input="$emit('update:title', $event.target.value)"
      />
    </div>
    <div class="ml-auto flex flex-wrap items-center justify-end gap-2">
      <template v-if="hasCards && selectedCount > 0">
        <slot name="extra"></slot>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="text-xs font-semibold text-slate-500 hover:text-primary"
            @click="$emit('select-all', true)"
          >
            全选</button
          ><span class="text-xs text-slate-300">/</span
          ><button
            type="button"
            class="text-xs font-semibold text-slate-500 hover:text-slate-700"
            @click="$emit('select-all', false)"
          >
            全不选
          </button>
        </div>
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-white hover:bg-secondary disabled:opacity-60"
          :disabled="selectedCount === 0 || downloading"
          @click="$emit('download')"
        >
          <RefreshCw v-if="downloading" class="h-3.5 w-3.5 animate-spin" /><Download
            v-else
            class="h-3.5 w-3.5"
          />{{ downloading ? '打包中...' : `批量下载 (${selectedCount}${mediaUnit})` }}
        </button>
        <div class="h-4 w-px bg-slate-200"></div>
      </template>
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-lg border border-primary/30 bg-white px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/5 disabled:opacity-50"
        :disabled="generating"
        @click="$emit('create')"
      >
        <Plus class="h-3.5 w-3.5" />新建任务
      </button>
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:border-primary/40 hover:text-primary"
        @click="$emit('history')"
      >
        <Clock3 class="h-3.5 w-3.5" />生成记录
      </button>
    </div>
  </div>
</template>
