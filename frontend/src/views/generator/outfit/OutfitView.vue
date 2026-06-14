<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/GenerationPreviewModal.vue'
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import OutfitSettingsPanel from '@/components/outfit/OutfitSettingsPanel.vue'
import { useOutfitGenerator } from '@/composables/useOutfitGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'
import { deleteGenerationJob } from '@/api/generation.js'
import { deleteImageTask, regenerateImageTask } from '@/api/image.js'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const outfit = useOutfitGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/outfit/${jobId}`)
  },
})

const editModalOpen = ref(false)
const editCard = ref(null)
const editSubmitting = ref(false)

async function openHistory() {
  outfit.showHistoryDrawer.value = true
  await outfit.loadHistoryTasks()
}

function pickHistory(jobId) {
  outfit.showHistoryDrawer.value = false
  router.push(`/generator/outfit/${jobId}`)
}

async function handleCreateNewTask() {
  const ok = await outfit.createNewTask()
  if (ok) {
    router.push('/generator/outfit')
  }
}

async function handleRouteJobId(jobId) {
  if (jobId && jobId !== outfit.currentJobId.value) {
    const ok = await outfit.loadGenerationJob(jobId)
    if (!ok) {
      router.replace('/generator/outfit')
    }
  } else if (!jobId && outfit.currentJobId.value) {
    outfit.resetWorkspaceToDraft()
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
    const idx = outfit.historyTasks.value.findIndex((t) => t.job_id === job.job_id)
    if (idx > -1) outfit.historyTasks.value.splice(idx, 1)
    if (job.job_id === outfit.currentJobId.value) {
      outfit.resetWorkspaceToDraft()
      router.push('/generator/outfit')
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

    const target = outfit.outputCards.value.find((c) => c.taskId === card.taskId)
    if (target) {
      target.id = newTaskId
      target.taskId = newTaskId
      target.previousResultUrl = target.resultUrl || target.dataUrl || ''
      target.dataUrl = ''
      target.resultUrl = ''
      target.status = 'processing'
      target.errorMessage = ''
      target.userPrompt = prompt
    }
    closeEditModal()
    toast.success('已提交重新生成，请稍候...')
    if (target) {
      outfit.startPollingCard(target)
    }
  } catch {
    toast.error('重新生成失败，请稍后重试')
    editSubmitting.value = false
  }
}

async function handleDeleteCard() {
  const card = editCard.value
  if (!card) return
  const ok = await confirm.open({
    title: '删除图片',
    message: '确定删除这张图片吗？图片不会立即从存储中物理删除。',
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
    const idx = outfit.outputCards.value.findIndex((c) => c.id === card.id)
    if (idx > -1) outfit.outputCards.value.splice(idx, 1)
    closeEditModal()
    toast.success('图片已删除')
  } catch {
    toast.error('删除失败，请稍后重试')
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
    const idx = outfit.outputCards.value.findIndex((c) => c.id === card.id)
    if (idx > -1) outfit.outputCards.value.splice(idx, 1)
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
    <OutfitSettingsPanel
      :settings="outfit.settings"
      :garment-images="outfit.garmentImages.value"
      :main-garment-index="outfit.mainGarmentIndex.value"
      :models="outfit.modelLibrary.value"
      :models-loading="outfit.modelsLoading.value"
      :selected-model-id="outfit.selectedModelId.value"
      :selected-scenes="outfit.selectedScenes.value"
      :scene-description="outfit.sceneDescription.value"
      :selected-image-label="outfit.selectedImageLabel.value"
      :loading="outfit.generating.value"
      :can-generate="outfit.canGenerate.value"
      @update:settings="Object.assign(outfit.settings, $event)"
      @update:garment-images="outfit.garmentImages.value = $event"
      @update:main-garment-index="outfit.mainGarmentIndex.value = $event"
      @update:selected-model-id="outfit.selectedModelId.value = $event"
      @update:selected-scenes="outfit.selectedScenes.value = $event"
      @update:scene-description="outfit.sceneDescription.value = $event"
      @notify="outfit.showNotice"
      @generate-images="outfit.generateOutfitImages"
    />

    <GenerationWorkspace
      :settings="outfit.settings"
      :current-task-title="outfit.currentTaskTitle.value"
      :output-cards="outfit.outputCards.value"
      :generating="outfit.generating.value"
      :generated-count="outfit.generatedCount.value"
      :total-count="outfit.totalCount.value"
      :job-total="outfit.jobTotal.value"
      :gen-logs="outfit.genLogs.value"
      :selected-cards-count="outfit.selectedCardsCount.value"
      :selected-image-label="outfit.selectedImageLabel.value"
      :get-module-name="outfit.getSceneName"
      title-badge="本次穿搭任务"
      empty-title="服饰穿搭"
      empty-subtitle="上传服装图，选择模特和拍摄场景，一次生成多张穿搭图。"
      :empty-slides="outfit.previewSlides.value"
      loading-title="AI 服饰穿搭图生成中"
      progress-text="正在生成服饰穿搭图"
      @update:current-task-title="outfit.updateCurrentJobTitle"
      @select-all-cards="outfit.toggleSelectAllCards"
      @batch-download="outfit.batchDownload"
      @toggle-card="outfit.toggleCardSelection"
      @download-card="outfit.downloadSingleImage"
      @edit-card="openEditModal"
      @zoom-card="(card) => { outfit.zoomCard.value = card }"
      @delete-card="handleDeleteCardDirect"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="outfit.showHistoryDrawer.value"
      :jobs="outfit.historyTasks.value"
      :loading="outfit.historyLoading.value"
      :current-job-id="outfit.currentJobId.value"
      @close="outfit.showHistoryDrawer.value = false"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="outfit.zoomCard.value"
      title="服饰穿搭大图预览"
      alt="服饰穿搭预览"
      @close="outfit.zoomCard.value = null"
    />

    <ImageEditModal
      :open="editModalOpen"
      :card="editCard"
      :module-name="editCard ? outfit.getSceneName(editCard.typeId) : ''"
      :submitting="editSubmitting"
      @close="closeEditModal"
      @submit="handleRegenerate"
      @delete="handleDeleteCard"
    />
  </GeneratorLayout>
</template>
