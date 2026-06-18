<script setup>
import { onMounted } from 'vue'
import { Download, ImageOff, LoaderCircle, Trash2 } from 'lucide-vue-next'
import AppModal from '@/components/ui/AppModal.vue'
import AppCheckbox from '@/components/ui/AppCheckbox.vue'
import AssetCardGrid from '@/components/assets/AssetCardGrid.vue'
import GeneratorLayout from '@/components/layout/GeneratorLayout.vue'
import { useAssetLibrary } from '@/composables/useAssetLibrary.js'
import { useConfirm } from '@/composables/useConfirm.js'

const confirm = useConfirm()

const {
  assets,
  loading,
  total,
  page,
  pageSize,
  scenario,
  totalPages,
  zoomCard,
  selectedCards,
  selectedCardsCount,
  toggleCardSelection,
  toggleSelectAllCards,
  batchDownload,
  downloadAsset,
  loadAssets,
  changeScenario,
  changePage,
  deleteSelected,
  SCENARIO_OPTIONS,
} = useAssetLibrary()

const SCENARIO_LABEL_MAP = {
  product_suite: '商品套图',
  product_image: '商品详情图',
  outfit: '服饰穿搭',
  free_image: '自由生图',
  product_video: '商品视频',
}

function getScenarioLabel(card) {
  return SCENARIO_LABEL_MAP[card.scenario] || ''
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
    title: card.mediaType === 'video' ? '删除视频' : '删除图片',
    message: `确定永久删除这个${card.mediaType === 'video' ? '视频' : '图片'}资产吗？此操作不可撤销。`,
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
      <header class="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div class="flex items-center gap-4">
          <h1 class="text-base font-bold text-slate-800">资产库</h1>
          <!-- 场景筛选 -->
          <nav class="flex gap-1 rounded-lg bg-slate-100 p-0.5">
            <button
              v-for="opt in SCENARIO_OPTIONS"
              :key="opt.value"
              type="button"
              class="rounded-md px-3 py-1.5 text-xs font-medium transition-all"
              :class="scenario === opt.value
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'"
              @click="changeScenario(opt.value)"
            >
              {{ opt.label }}
            </button>
          </nav>
          <span class="text-xs text-slate-400">共 {{ total }} 个</span>
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
            :disabled="selectedCardsCount === 0"
            @click="batchDownload"
          >
            <Download class="h-3.5 w-3.5" />
            下载 ({{ selectedCardsCount }})
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
          <p class="mt-1 text-xs text-slate-400">完成图片或视频生成后，资源将自动出现在这里</p>
        </div>

        <!-- 卡片网格 -->
        <AssetCardGrid
          v-else
          :cards="assets"
          :scenario-label="getScenarioLabel"
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
        <img
          v-else
          :src="zoomCard.dataUrl"
          referrerpolicy="no-referrer"
          class="max-h-[85vh] max-w-full object-contain"
          alt="大图预览"
        />
      </div>
    </AppModal>
  </GeneratorLayout>
</template>
