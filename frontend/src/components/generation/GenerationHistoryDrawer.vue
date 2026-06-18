<script setup>
import { Trash2 } from 'lucide-vue-next'
import AppDrawer from '@/components/ui/AppDrawer.vue'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  jobs: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  currentJobId: {
    type: String,
    default: '',
  },
  emptyHint: {
    type: String,
    default: '点击「+ 新建任务」开始你的第一次生成',
  },
  unit: {
    type: String,
    default: '张',
  },
})

const emit = defineEmits(['close', 'pick', 'delete'])

const STATUS_LABEL = {
  draft: '草稿',
  generating: '生成中',
  done: '已完成',
  partial_failed: '部分失败',
  failed: '失败',
  timeout: '超时',
}

function getStatusLabel(job) {
  const key = job.display_status || job.status || 'draft'
  return STATUS_LABEL[key] || key
}

function formatTime(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<template>
  <AppDrawer
    :open="open"
    title="生成记录"
    subtitle="选择历史任务可恢复到当前工作区"
    @close="emit('close')"
  >
    <div v-if="loading" class="flex items-center justify-center py-8 text-xs text-slate-400">
      正在加载...
    </div>
    <div v-else-if="jobs.length === 0" class="flex flex-col items-center justify-center gap-2 py-12 text-center text-xs text-slate-400">
      <span>暂无生成记录</span>
      <span>{{ emptyHint }}</span>
    </div>
    <ul v-else class="space-y-2">
      <li
        v-for="job in jobs"
        :key="job.job_id"
        class="group cursor-pointer rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-xs transition-all hover:border-primary/40 hover:bg-primary/5"
        :class="{ 'border-primary/60 bg-primary/5': job.job_id === currentJobId }"
        @click="emit('pick', job.job_id)"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="truncate font-bold text-slate-800">{{ job.title }}</span>
          <div class="flex shrink-0 items-center gap-1.5">
            <button
              type="button"
              class="rounded p-0.5 text-slate-300 opacity-0 transition-all hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100"
              title="删除任务"
              @click.stop="emit('delete', job)"
            >
              <Trash2 class="h-3.5 w-3.5" />
            </button>
            <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
              {{ getStatusLabel(job) }}
            </span>
          </div>
        </div>
        <div class="mt-1.5 flex items-center justify-between text-[11px] text-slate-500">
          <span>{{ formatTime(job.created_at) }}</span>
          <span>
            共 {{ job.total }} {{ unit }}
            <span v-if="job.completed > 0" class="text-primary">· {{ job.completed }} 完成</span>
            <span v-if="job.failed > 0" class="text-rose-500">· {{ job.failed }} 失败</span>
          </span>
        </div>
      </li>
    </ul>
  </AppDrawer>
</template>
