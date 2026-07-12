<script setup>
import { onMounted } from 'vue'
import {
  Download,
  FileAudio,
  ImageOff,
  Images,
  LayoutGrid,
  LoaderCircle,
  Trash2,
  Video,
} from 'lucide-vue-next'
import AppModal from '@/components/ui/AppModal.vue'
import AppCheckbox from '@/components/ui/AppCheckbox.vue'
import AppTabNav from '@/components/ui/AppTabNav.vue'
import AssetCardGrid from '@/components/assets/AssetCardGrid.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import { useAssetLibrary } from '@/composables/useAssetLibrary.js'
import { useConfirm } from '@/composables/useConfirm.js'
import { scenarioIcons as generationScenarioIcons, scenarioLabelMap } from '@/constants/scenarios.js'

const confirm = useConfirm()

const {
  assets,
  loading,
  total,
  page,
  pageSize,
  mediaType,
  scenario,
  totalPages,
  scenarioFilters,
  zoomCard,
  selectedCardsCount,
  toggleCardSelection,
  toggleSelectAllCards,
  batchDownload,
  downloadAsset,
  loadAssets,
  changeMediaType,
  changeScenario,
  changePage,
  deleteSelected,
  mediaTypeOptions,
} = useAssetLibrary()

const scenarioIcons = {
  "": LayoutGrid,
  ...generationScenarioIcons,
}
const mediaTypeIcons = {
  "": LayoutGrid,
  image: Images,
  video: Video,
  audio: FileAudio,
}

function getScenarioLabel(card) {
  return scenarioLabelMap[card.scenario] || ''
}

function getMediaLabel(card) {
  if (card.mediaType === 'video') return '视频'
  if (card.mediaType === 'audio') return '音频'
  return '图片'
}

function isAllSelected() {
  return assets.value.length > 0 && assets.value.every((c) => c.selected)
}

function handleToggleAll(checked) {
  toggleSelectAllCards(checked)
}

async function handleBatchDelete() {
  if (selectedCardsCount.value === 0) return
  const ok = await confirm.open({
    title: '批量删除',
    message: `确定永久删除选中的 ${selectedCardsCount.value} 个资产吗？此操作不可撤销。`,
    confirmText: '删除',
    cancelText: '取消',
    tone: 'danger',
  })
  if (!ok) return
  await deleteSelected()
}

async function handleDeleteSingle(card) {
  const ok = await confirm.open({
    title: `删除${getMediaLabel(card)}`,
    message: `确定永久删除这个${getMediaLabel(card)}资产吗？此操作不可撤销。`,
    confirmText: '删除',
    cancelText: '取消',
    tone: 'danger',
  })
  if (!ok) return
  // 临时选中该卡片来复用 deleteSelected
  const wasSelected = card.selected
  card.selected = true
  // 取消其他卡片选中
  const others = assets.value.filter((c) => c.id !== card.id && c.selected)
  others.forEach((c) => { c.selected = false })
  await deleteSelected()
  // 恢复其他选中状态
  others.forEach((c) => { c.selected = true })
  if (!wasSelected) card.selected = false
}

function handleZoom(card) {
  zoomCard.value = card
}

onMounted(() => {
  loadAssets()
})
</script>

<template>
  <GeneratorLayout>
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- 顶部工具栏 -->
      <header class="space-y-2 border-b border-slate-200 bg-white px-6 py-3">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-3">
          <h1 class="text-base font-bold text-slate-800">资产库</h1>
            <span class="text-xs font-semibold text-slate-400">共 {{ total }} 个</span>
          </div>
          <div class="flex items-center gap-3">
            <!-- 全选 -->
            <AppCheckbox
              :model-value="isAllSelected()"
              label="全选"
              size="sm"
              :disabled="assets.length === 0"
              @change="handleToggleAll"
            />
            <!-- 批量下载 -->
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="selectedCardsCount === 0 || downloading"
              @click="batchDownload"
            >
              <LoaderCircle v-if="downloading" class="h-3.5 w-3.5 animate-spin" />
              <Download v-else class="h-3.5 w-3.5" />
              {{ downloading ? '下载中...' : `下载 (${selectedCardsCount})` }}
            </button>
            <!-- 批量删除 -->
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-600 transition-colors hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="selectedCardsCount === 0"
              @click="handleBatchDelete"
            >
              <Trash2 class="h-3.5 w-3.5" />
              删除 ({{ selectedCardsCount }})
            </button>
          </div>
        </div>
        <div class="flex min-w-0 flex-col items-start gap-2">
          <AppTabNav
            :tabs="mediaTypeOptions"
            :active-key="mediaType"
            :icons="mediaTypeIcons"
            @change="changeMediaType"
          />
          <AppTabNav
            v-if="scenarioFilters.length"
            :tabs="scenarioFilters"
            :active-key="scenario"
            :icons="scenarioIcons"
            @change="changeScenario"
          />
        </div>
      </header>

      <!-- 内容区 -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Loading -->
        <div v-if="loading && assets.length === 0" class="flex flex-col items-center justify-center py-20">
          <LoaderCircle class="h-8 w-8 animate-spin text-primary" />
          <span class="mt-3 text-sm text-slate-500">加载中...</span>
        </div>

        <!-- 空状态 -->
        <div v-else-if="!loading && assets.length === 0" class="flex flex-col items-center justify-center py-20">
          <ImageOff class="h-12 w-12 text-slate-300" />
          <p class="mt-3 text-sm text-slate-500">暂无资产</p>
          <p class="mt-1 text-xs text-slate-400">完成生成或上传后，图片、视频和音频将自动出现在这里</p>
        </div>

        <!-- 卡片网格 -->
        <AssetCardGrid
          v-else
          :cards="assets"
          :scenario-label="getScenarioLabel"
          :downloading="downloading"
          @toggle-card="toggleCardSelection"
          @download-card="downloadAsset"
          @zoom-card="handleZoom"
          @delete-card="handleDeleteSingle"
        />

        <!-- 分页 -->
        <div v-if="total > pageSize" class="mt-6 flex items-center justify-center gap-2">
          <button
            type="button"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="page <= 1"
            @click="changePage(page - 1)"
          >
            上一页
          </button>
          <span class="text-xs text-slate-500">{{ page }} / {{ totalPages }}</span>
          <button
            type="button"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 大图弹窗 -->
    <AppModal :open="!!zoomCard" panel-class="max-w-[90vw] max-h-[90vh] w-auto" @close="zoomCard = null">
      <div v-if="zoomCard" class="flex items-center justify-center p-2">
        <video
          v-if="zoomCard.mediaType === 'video'"
          :src="zoomCard.dataUrl"
          class="max-h-[85vh] max-w-full object-contain"
          controls
          autoplay
          playsinline
        ></video>
        <div v-else-if="zoomCard.mediaType === 'audio'" class="flex min-w-[320px] flex-col items-center gap-4 p-6">
          <FileAudio class="h-12 w-12 text-primary" />
          <audio :src="zoomCard.resultUrl || zoomCard.dataUrl" controls autoplay preload="metadata" class="w-full"></audio>
        </div>
        <img
          v-else
          :src="zoomCard.previewUrl || zoomCard.resultUrl || zoomCard.dataUrl"
          referrerpolicy="no-referrer"
          class="max-h-[85vh] max-w-full object-contain"
          alt="大图预览"
        />
      </div>
    </AppModal>
  </GeneratorLayout>
</template>
