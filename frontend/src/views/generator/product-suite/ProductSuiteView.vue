<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageEditModal from '@/components/generation/ImageEditModal.vue'
import GenerationHistoryDrawer from '@/components/generation/GenerationHistoryDrawer.vue'
import GenerationPreviewModal from '@/components/generation/GenerationPreviewModal.vue'
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import ProductSuiteSettingsPanel from '@/components/product-suite/ProductSuiteSettingsPanel.vue'
import { useProductSuiteGenerator } from '@/composables/useProductSuiteGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'
import { productSuitePreviewSlides } from '@/constants/productSuite.js'
import { deleteGenerationJob } from '@/api/generation.js'
import { deleteImageTask, regenerateImageTask } from '@/api/image.js'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const suite = useProductSuiteGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/product-suite/${jobId}`)
  },
})

// 编辑弹窗状态
const editModalOpen = ref(false)
const editCard = ref(null)
const editSubmitting = ref(false)

async function openHistory() {
  suite.showHistoryDrawer.value = true
  await suite.loadHistoryTasks()
}

function pickHistory(jobId) {
  suite.showHistoryDrawer.value = false
  router.push(`/generator/product-suite/${jobId}`)
}

async function handleCreateNewTask() {
  const ok = await suite.createNewTask()
  if (ok) {
    router.push('/generator/product-suite')
  }
}

async function handleRouteJobId(jobId) {
  if (jobId && jobId !== suite.currentJobId.value) {
    const ok = await suite.loadGenerationJob(jobId)
    if (!ok) {
      router.replace('/generator/product-suite')
    }
  } else if (!jobId && suite.currentJobId.value) {
    suite.resetWorkspaceToDraft()
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
    const idx = suite.historyTasks.value.findIndex((t) => t.job_id === job.job_id)
    if (idx > -1) suite.historyTasks.value.splice(idx, 1)
    if (job.job_id === suite.currentJobId.value) {
      suite.resetWorkspaceToDraft()
      router.push('/generator/product-suite')
    }
    toast.success('任务已删除')
  } catch {
    toast.error('删除失败，请稍后重试')
  }
}

// --- 编辑弹窗 ---
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

    // 更新 card 状态 —— 先找到 outputCards 中的原始对象确保响应式
    const target = suite.outputCards.value.find((c) => c.taskId === card.taskId)
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
    // 开始轮询
    if (target) {
      suite.startPollingCard(target)
    }
  } catch (err) {
    console.error('[regenerate]', err)
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
    // 从 outputCards 中移除
    const idx = suite.outputCards.value.findIndex((c) => c.id === card.id)
    if (idx > -1) suite.outputCards.value.splice(idx, 1)
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
    const idx = suite.outputCards.value.findIndex((c) => c.id === card.id)
    if (idx > -1) suite.outputCards.value.splice(idx, 1)
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
    <ProductSuiteSettingsPanel
      :settings="suite.settings"
      :uploaded-images="suite.uploadedImages.value"
      :main-image-index="suite.mainImageIndex.value"
      :suite-structure="suite.suiteStructure.value"
      :ai-loading="suite.aiLoading.value"
      :can-generate="suite.canGenerate.value"
      :generating="suite.generating.value"
      :generated-count="suite.generatedCount.value"
      :total-count="suite.totalCount.value"
      :job-total="suite.jobTotal.value"
      :selected-image-label="suite.selectedImageLabel.value"
      :generate-selling-points="suite.generateSellingPointsWithAI"
      @update:settings="Object.assign(suite.settings, $event)"
      @update:uploaded-images="suite.uploadedImages.value = $event"
      @update:main-image-index="suite.mainImageIndex.value = $event"
      @update:suite-structure="suite.suiteStructure.value = $event"
      @notify="suite.showNotice"
      @generate="suite.generateSuiteImages"
    />

    <GenerationWorkspace
      :settings="suite.settings"
      :current-task-title="suite.currentTaskTitle.value"
      :output-cards="suite.outputCards.value"
      :generating="suite.generating.value"
      :generated-count="suite.generatedCount.value"
      :total-count="suite.totalCount.value"
      :job-total="suite.jobTotal.value"
      :gen-logs="suite.genLogs.value"
      :selected-cards-count="suite.selectedCardsCount.value"
      :selected-image-label="suite.selectedImageLabel.value"
      :get-module-name="suite.getStructureName"
      title-badge="本次套图任务"
      empty-title="AI商品套图"
      empty-subtitle="上传商品图，AI 即刻生成符合多电商平台规范的高转化率商品套图。"
      :empty-slides="productSuitePreviewSlides"
      loading-title="AI 商品套图生成中"
      progress-text="正在生成商品套图"
      @update:current-task-title="suite.updateCurrentJobTitle"
      @select-all-cards="suite.toggleSelectAllCards"
      @batch-download="suite.batchDownload"
      @toggle-card="suite.toggleCardSelection"
      @download-card="suite.downloadSingleImage"
      @edit-card="openEditModal"
      @zoom-card="(card) => { suite.zoomCard.value = card }"
      @delete-card="handleDeleteCardDirect"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="suite.showHistoryDrawer.value"
      :jobs="suite.historyTasks.value"
      :loading="suite.historyLoading.value"
      :current-job-id="suite.currentJobId.value"
      @close="suite.showHistoryDrawer.value = false"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="suite.zoomCard.value"
      title="商品套图大图预览"
      alt="商品套图预览"
      @close="suite.zoomCard.value = null"
    />

    <ImageEditModal
      :open="editModalOpen"
      :card="editCard"
      :module-name="editCard ? suite.getStructureName(editCard.typeId) : ''"
      :submitting="editSubmitting"
      @close="closeEditModal"
      @submit="handleRegenerate"
      @delete="handleDeleteCard"
    />
  </GeneratorLayout>
</template>
