<script setup>
import { Archive, Lock } from 'lucide-vue-next'
import AppDrawer from '@/components/ui/AppDrawer.vue'
import AppModal from '@/components/ui/AppModal.vue'

defineProps({
  showLongPreviewModal: {
    type: Boolean,
    default: false,
  },
  showHistoryDrawer: {
    type: Boolean,
    default: false,
  },
  showQueueDrawer: {
    type: Boolean,
    default: false,
  },
  zoomCard: {
    type: Object,
    default: null,
  },
  selectedCards: {
    type: Array,
    required: true,
  },
  selectedCardsCount: {
    type: Number,
    default: 0,
  },
  longPreviewHeight: {
    type: Number,
    default: 0,
  },
  historyTasks: {
    type: Array,
    required: true,
  },
  taskQueue: {
    type: Array,
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
  getProgressWidthClass: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'close-long-preview',
  'download-long-image',
  'close-history',
  'load-history',
  'close-queue',
  'close-zoom',
])
</script>

<template>
  <AppModal
    :open="showLongPreviewModal"
    title="详情页长图拼接预览"
    :subtitle="`已将选中的 ${selectedCardsCount} 张主图无缝拼接为垂直排版长图`"
    panel-class="w-full max-w-lg h-[90vh]"
    @close="emit('close-long-preview')"
  >
    <div class="flex flex-1 justify-center overflow-y-auto bg-slate-100 p-8">
      <div class="flex w-72 flex-col divide-y divide-slate-100 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
        <img v-for="card in selectedCards" :key="card.id" :src="card.dataUrl" class="w-full object-contain" alt="主图片段" />
      </div>
    </div>
    <div class="flex shrink-0 items-center justify-between border-t border-slate-100 bg-slate-50/50 px-5 py-3">
      <span class="text-xs font-medium text-slate-400">总高度约 {{ longPreviewHeight }} 像素</span>
      <button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white shadow transition-all hover:bg-secondary" @click="emit('download-long-image')">
        下载无损长图 (PNG)
      </button>
    </div>
  </AppModal>

  <AppDrawer :open="showHistoryDrawer" title="历史生成记录" @close="emit('close-history')">
    <div class="space-y-3">
      <button
        v-for="history in historyTasks"
        :key="history.id"
        type="button"
        class="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-left shadow-sm transition-colors hover:border-primary/40 hover:bg-primary/5"
        @click="emit('load-history', history)"
      >
        <div class="mb-1.5 flex items-start justify-between gap-2">
          <span class="max-w-[200px] truncate text-xs font-bold text-slate-800">{{ history.title }}</span>
          <span class="rounded border border-primary/10 bg-primary/10 px-1.5 py-0.5 text-xs font-bold text-primary">{{ history.cardsCount }}张主图</span>
        </div>
        <div class="flex items-center justify-between text-xs text-slate-500">
          <span>渠道：{{ history.platform }}</span>
          <span>{{ history.time }}</span>
        </div>
      </button>

      <div v-if="historyTasks.length === 0" class="flex h-64 flex-col items-center justify-center text-center text-slate-400">
        <Lock class="mb-2 h-10 w-10 opacity-50" />
        <span class="text-xs">暂无历史排版任务</span>
      </div>
    </div>
  </AppDrawer>

  <AppDrawer :open="showQueueDrawer" title="批量任务挂机后台" subtitle="异步排队，生成完成后支持邮件与系统通知" @close="emit('close-queue')">
    <div class="space-y-3">
      <div v-for="task in taskQueue" :key="task.id" class="rounded-xl border border-slate-200 bg-slate-50 p-3 shadow-sm">
        <div class="mb-1.5 flex items-center justify-between gap-2">
          <span class="max-w-[180px] truncate text-xs font-bold text-slate-800">{{ task.title }}</span>
          <span class="rounded px-1.5 py-0.5 text-xs font-bold" :class="task.status === '进行中' ? 'border border-amber-100 bg-amber-50 text-amber-600' : 'border border-primary/10 bg-primary/10 text-primary'">
            {{ task.status }}
          </span>
        </div>
        <div class="mb-2 h-1 overflow-hidden rounded-full bg-slate-200">
          <div class="h-full rounded-full transition-all duration-300" :class="[task.status === '进行中' ? 'bg-amber-500' : 'bg-primary', getProgressWidthClass(task.progress)]"></div>
        </div>
        <div class="flex justify-between text-xs text-slate-500">
          <span>渠道：{{ task.platform }} ({{ task.ratio }})</span>
          <span>进度：{{ task.progress }}%</span>
        </div>
      </div>

      <div v-if="taskQueue.length === 0" class="flex h-64 flex-col items-center justify-center text-center text-slate-400">
        <Archive class="mb-2 h-10 w-10 opacity-50" />
        <span class="text-xs">暂无后台批量挂机任务</span>
      </div>
    </div>
  </AppDrawer>

  <AppModal :open="Boolean(zoomCard)" panel-class="max-w-3xl max-h-[90vh]" @close="emit('close-zoom')">
    <div v-if="zoomCard" class="relative flex flex-col bg-white p-4">
      <img :src="zoomCard.dataUrl" class="max-h-[75vh] max-w-full rounded-xl border border-slate-100 object-contain shadow-inner" alt="放大主图" />
      <div class="mt-4 text-center">
        <h4 class="text-sm font-bold text-slate-800">{{ getModuleName(zoomCard.typeId) }}</h4>
        <p class="mt-1 text-xs font-bold text-primary">策略设计：{{ getModuleStrategy(zoomCard.typeId) }}</p>
      </div>
    </div>
  </AppModal>
</template>
