<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppDrawer from '@/components/AppDrawer.vue'
import AppModal from '@/components/AppModal.vue'
import GeneratorLayout from '@/components/GeneratorLayout.vue'
import ProductSuiteSettingsPanel from '@/components/ProductSuiteSettingsPanel.vue'
import ProductSuiteWorkspace from '@/components/ProductSuiteWorkspace.vue'
import { useProductSuiteGenerator } from '@/composables/useProductSuiteGenerator.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { useToast } from '@/composables/useToast.js'
import { deleteGenerationJob } from '@/api/generation.js'
import { Trash2 } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const suite = useProductSuiteGenerator({
  onJobCreated(jobId) {
    router.replace(`/generator/product-suite/${jobId}`)
  },
})

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

const sortedHistory = computed(() => suite.historyTasks.value)

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
    // 从列表中移除
    const idx = suite.historyTasks.value.findIndex((t) => t.job_id === job.job_id)
    if (idx > -1) suite.historyTasks.value.splice(idx, 1)
    // 如果删的是当前查看的任务，回到空工作台
    if (job.job_id === suite.currentJobId.value) {
      suite.resetWorkspaceToDraft()
      router.push('/generator/product-suite')
    }
    toast.success('任务已删除')
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

    <ProductSuiteWorkspace
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
      :get-structure-name="suite.getStructureName"
      :get-structure-strategy="suite.getStructureStrategy"
      @update:current-task-title="suite.updateCurrentJobTitle"
      @select-all-cards="suite.toggleSelectAllCards"
      @batch-download="suite.batchDownload"
      @toggle-card="suite.toggleCardSelection"
      @download-card="suite.downloadSingleImage"
      @regenerate-card="suite.regenerateSingleCard"
      @zoom-card="(card) => { if (card.status === 'done' && card.dataUrl) suite.zoomCard.value = card }"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <AppDrawer
      :open="suite.showHistoryDrawer.value"
      title="生成记录"
      subtitle="选择历史任务可恢复到当前工作区"
      @close="suite.showHistoryDrawer.value = false"
    >
      <div v-if="suite.historyLoading.value" class="flex items-center justify-center py-8 text-xs text-slate-400">
        正在加载...
      </div>
      <div v-else-if="sortedHistory.length === 0" class="flex flex-col items-center justify-center gap-2 py-12 text-center text-xs text-slate-400">
        <span>暂无生成记录</span>
        <span>点击「+ 新建任务」开始你的第一次生成</span>
      </div>
      <ul v-else class="space-y-2">
        <li
          v-for="job in sortedHistory"
          :key="job.job_id"
          class="group cursor-pointer rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-xs transition-all hover:border-primary/40 hover:bg-primary/5"
          :class="{ 'border-primary/60 bg-primary/5': job.job_id === suite.currentJobId.value }"
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
      :open="Boolean(suite.zoomCard.value)"
      title="商品套图大图预览"
      panel-class="w-full max-w-4xl"
      @close="suite.zoomCard.value = null"
    >
      <div v-if="suite.zoomCard.value" class="bg-slate-100 p-6">
        <img :src="suite.zoomCard.value.dataUrl" class="mx-auto max-h-[75vh] rounded-xl object-contain shadow-lg" alt="商品套图预览" />
      </div>
    </AppModal>
  </GeneratorLayout>
</template>
