<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Trash2 } from 'lucide-vue-next'
import AppDrawer from '@/components/ui/AppDrawer.vue'
import AppModal from '@/components/ui/AppModal.vue'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import FreeImageSettingsPanel from '@/components/free-image/FreeImageSettingsPanel.vue'
import { useFreeImageGenerator } from '@/composables/useFreeImageGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'
import { deleteGenerationJob } from '@/api/generation.js'
import { deleteImageTask, regenerateImageTask } from '@/api/image.js'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const generator = useFreeImageGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/free-image/${jobId}`)
  },
})

const editModalOpen = ref(false)
const editCard = ref(null)
const editSubmitting = ref(false)

const STATUS_LABEL = {
  draft: '草稿',
  generating: '生成中',
  done: '已完成',
  partial_failed: '部分失败',
  failed: '失败',
  timeout: '超时',
}

const sortedHistory = computed(() => generator.historyTasks.value)

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

async function openHistory() {
  generator.showHistoryDrawer.value = true
  await generator.loadHistoryTasks()
}

function pickHistory(jobId) {
  generator.showHistoryDrawer.value = false
  router.push(`/generator/free-image/${jobId}`)
}

async function handleCreateNewTask() {
  const ok = await generator.createNewTask()
  if (ok) {
    router.push('/generator/free-image')
  }
}

async function handleRouteJobId(jobId) {
  if (jobId && jobId !== generator.currentJobId.value) {
    const ok = await generator.loadGenerationJob(jobId)
    if (!ok) {
      router.replace('/generator/free-image')
    }
  } else if (!jobId && generator.currentJobId.value) {
    generator.resetWorkspaceToDraft()
  }
}

async function handleDeleteJob(job) {
  const displayStatus = job.display_status || job.status
  if (displayStatus === 'generating') {
    toast.info('任务生成中，暂不能删除')
    return
  }
  const ok = await confirm.open({
    title: '删除任务',
    message: '确定删除这个生成任务吗？已生成图片不会立即从存储中物理删除。',
    confirmText: '删除',
    cancelText: '取消',
    tone: 'danger',
  })
  if (!ok) return
  try {
    const res = await deleteGenerationJob(job.job_id)
    if (res.code !== 0) {
      toast.error(res.message || '删除失败')
      return
    }
    const idx = generator.historyTasks.value.findIndex((t) => t.job_id === job.job_id)
    if (idx > -1) generator.historyTasks.value.splice(idx, 1)
    if (job.job_id === generator.currentJobId.value) {
      generator.resetWorkspaceToDraft()
      router.push('/generator/free-image')
    }
    toast.success('任务已删除')
  } catch {
    toast.error('删除失败，请稍后重试')
  }
}

function openEditModal(card) {
  if (card.status !== 'done' || !card.dataUrl) return
  editCard.value = card
  editModalOpen.value = true
}

function closeEditModal() {
  editModalOpen.value = false
  editCard.value = null
  editSubmitting.value = false
}

async function handleRegenerate(userPrompt) {
  const prompt = (userPrompt || '').trim()
  if (!prompt) {
    toast.info('请输入用户提示词')
    return
  }
  const card = editCard.value
  if (!card) return
  if (!card.taskId) {
    toast.error('该图片缺少任务 ID，无法重新生成')
    return
  }

  editSubmitting.value = true
  try {
    const res = await regenerateImageTask(card.taskId, '', prompt)
    if (!res || res.code !== 0) {
      toast.error((res && res.message) || '重新生成失败')
      editSubmitting.value = false
      return
    }
    const newTaskId = res.data?.task_id
    if (!newTaskId) {
      toast.error('重新生成失败：缺少新任务 ID')
      editSubmitting.value = false
      return
    }

    const target = generator.outputCards.value.find((c) => c.taskId === card.taskId)
    if (target) {
      target.id = newTaskId
      target.taskId = newTaskId
      target.previousResultUrl = target.resultUrl || target.dataUrl || ''
      target.dataUrl = ''
      target.resultUrl = ''
      target.status = 'processing'
      target.errorMessage = ''
      target.userPrompt = prompt
      target.strategyContent = prompt
    }
    closeEditModal()
    toast.success('已提交重新生成，请稍候...')
    if (target) {
      generator.startPollingCard(target)
    }
  } catch {
    toast.error('重新生成失败，请稍后重试')
    editSubmitting.value = false
  }
}

async function handleDeleteCardDirect(card) {
  if (!card) return
  const ok = await confirm.open({
    title: '删除图片',
    message: '确定删除这张图片吗？',
    confirmText: '删除',
    cancelText: '取消',
    tone: 'danger',
  })
  if (!ok) return
  try {
    const res = await deleteImageTask(card.taskId)
    if (res.code !== 0) {
      toast.error(res.message || '删除失败')
      return
    }
    const idx = generator.outputCards.value.findIndex((c) => c.id === card.id)
    if (idx > -1) generator.outputCards.value.splice(idx, 1)
    if (editCard.value?.id === card.id) {
      closeEditModal()
    }
    toast.success('图片已删除')
  } catch {
    toast.error('删除失败，请稍后重试')
  }
}

onMounted(() => {
  const jobId = route.params.jobId
  if (jobId) {
    handleRouteJobId(jobId)
  }
})

watch(
  () => route.params.jobId,
  (newJobId) => {
    handleRouteJobId(newJobId)
  },
)
</script>

<template>
  <GeneratorLayout>
    <FreeImageSettingsPanel
      :settings="generator.settings"
      :reference-images="generator.referenceImages.value"
      :main-image-index="generator.mainImageIndex.value"
      :optimizing="generator.optimizing.value"
      :can-optimize="generator.canOptimize.value"
      :can-generate="generator.canGenerate.value"
      :generating="generator.generating.value"
      :generated-count="generator.generatedCount.value"
      :total-count="generator.totalCount.value"
      :job-total="generator.jobTotal.value"
      :selected-image-label="generator.selectedImageLabel.value"
      @update:settings="Object.assign(generator.settings, $event)"
      @update:reference-images="generator.referenceImages.value = $event"
      @update:main-image-index="generator.mainImageIndex.value = $event"
      @notify="generator.showNotice"
      @optimize="generator.optimizePrompt"
      @generate="generator.generateFreeImage"
    />

    <GenerationWorkspace
      :settings="generator.settings"
      :current-task-title="generator.currentTaskTitle.value"
      :output-cards="generator.outputCards.value"
      :generating="generator.generating.value"
      :generated-count="generator.generatedCount.value"
      :total-count="generator.totalCount.value"
      :job-total="generator.jobTotal.value"
      :gen-logs="generator.genLogs.value"
      :selected-cards-count="generator.selectedCardsCount.value"
      :selected-image-label="generator.selectedImageLabel.value"
      :get-module-name="generator.getModuleName"
      title-badge="本次自由生图"
      empty-title="自由生图"
      empty-subtitle="输入提示词，可选参考图，直接生成你想要的画面。"
      loading-title="AI 自由生图生成中"
      progress-text="正在生成自由生图"
      @update:current-task-title="generator.updateCurrentJobTitle"
      @select-all-cards="generator.toggleSelectAllCards"
      @batch-download="generator.batchDownload"
      @toggle-card="generator.toggleCardSelection"
      @download-card="generator.downloadSingleImage"
      @edit-card="openEditModal"
      @zoom-card="(card) => { generator.zoomCard.value = card }"
      @delete-card="handleDeleteCardDirect"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <AppDrawer
      :open="generator.showHistoryDrawer.value"
      title="生成记录"
      subtitle="选择历史任务可恢复到当前工作区"
      @close="generator.showHistoryDrawer.value = false"
    >
      <div v-if="generator.historyLoading.value" class="flex items-center justify-center py-8 text-xs text-slate-400">
        正在加载...
      </div>
      <div v-else-if="sortedHistory.length === 0" class="flex flex-col items-center justify-center gap-2 py-12 text-center text-xs text-slate-400">
        <span>暂无生成记录</span>
        <span>输入提示词后点击「生成图片」开始第一次自由生图</span>
      </div>
      <ul v-else class="space-y-2">
        <li
          v-for="job in sortedHistory"
          :key="job.job_id"
          class="group cursor-pointer rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-xs transition-all hover:border-primary/40 hover:bg-primary/5"
          :class="{ 'border-primary/60 bg-primary/5': job.job_id === generator.currentJobId.value }"
          @click="pickHistory(job.job_id)"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="truncate font-bold text-slate-800">{{ job.title }}</span>
            <div class="flex shrink-0 items-center gap-1.5">
              <button
                type="button"
                class="rounded p-0.5 text-slate-300 opacity-0 transition-all hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100"
                title="删除任务"
                @click.stop="handleDeleteJob(job)"
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
              共 {{ job.total }} 张
              <span v-if="job.completed > 0" class="text-primary">· {{ job.completed }} 完成</span>
              <span v-if="job.failed > 0" class="text-rose-500">· {{ job.failed }} 失败</span>
            </span>
          </div>
        </li>
      </ul>
    </AppDrawer>

    <AppModal
      :open="Boolean(generator.zoomCard.value)"
      title="自由生图大图预览"
      panel-class="w-full max-w-4xl"
      @close="generator.zoomCard.value = null"
    >
      <div v-if="generator.zoomCard.value" class="bg-slate-100 p-6">
        <img :src="generator.zoomCard.value.dataUrl" class="mx-auto max-h-[75vh] rounded-xl object-contain shadow-lg" alt="自由生图预览" />
      </div>
    </AppModal>

    <ImageEditModal
      :open="editModalOpen"
      :card="editCard"
      module-name="自由生图"
      :submitting="editSubmitting"
      @close="closeEditModal"
      @submit="handleRegenerate"
      @delete="handleDeleteCardDirect(editCard)"
    />
  </GeneratorLayout>
</template>
