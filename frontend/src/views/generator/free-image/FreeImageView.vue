<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/GenerationPreviewModal.vue'
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

    <GenerationHistoryDrawer
      :open="generator.showHistoryDrawer.value"
      :jobs="generator.historyTasks.value"
      :loading="generator.historyLoading.value"
      :current-job-id="generator.currentJobId.value"
      empty-hint="输入提示词后点击「生成图片」开始第一次自由生图"
      @close="generator.showHistoryDrawer.value = false"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="generator.zoomCard.value"
      title="自由生图大图预览"
      alt="自由生图预览"
      @close="generator.zoomCard.value = null"
    />

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
