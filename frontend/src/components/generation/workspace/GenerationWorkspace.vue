<script setup>
import { Clock3, Download, ImageIcon, Plus, RefreshCw } from 'lucide-vue-next'
import GeneratedCardGrid from '@/components/generation/cards/GeneratedCardGrid.vue'
import GeneratorPreviewShowcase from '@/components/generation/workspace/GeneratorPreviewShowcase.vue'
import GeneratorWorkspaceShell from '@/components/generation/workspace/GeneratorWorkspaceShell.vue'
import VideoGeneratedCardGrid from '@/components/generation/cards/VideoGeneratedCardGrid.vue'
import AudioGeneratedCardGrid from '@/components/generation/cards/AudioGeneratedCardGrid.vue'

defineProps({
  settings: {
    type: Object,
    required: true,
  },
  currentTaskTitle: {
    type: String,
    required: true,
  },
  outputCards: {
    type: Array,
    required: true,
  },
  generating: {
    type: Boolean,
    default: false,
  },
  creatingBatch: {
    type: Boolean,
    default: false,
  },
  generatedCount: {
    type: Number,
    default: 0,
  },
  runningCount: {
    type: Number,
    default: 0,
  },
  failedCount: {
    type: Number,
    default: 0,
  },
  totalCount: {
    type: Number,
    default: 0,
  },
  jobTotal: {
    type: Number,
    default: 0,
  },
  genLogs: {
    type: Array,
    required: true,
  },
  selectedCardsCount: {
    type: Number,
    default: 0,
  },
  downloading: {
    type: Boolean,
    default: false,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  getModuleName: {
    type: Function,
    required: true,
  },
  titleBadge: {
    type: String,
    default: '本次生成任务',
  },
  emptyTitle: {
    type: String,
    default: 'AI 生图工作台',
  },
  emptySubtitle: {
    type: String,
    default: '配置生成参数后，AI 将在这里输出图片结果。',
  },
  emptySlides: {
    type: Array,
    default: () => [],
  },
  mediaType: {
    type: String,
    default: 'image',
  },
  mediaUnit: {
    type: String,
    default: '张',
  },
  loadingTitle: {
    type: String,
    default: 'AI 图片生成中',
  },
  loadingDescription: {
    type: String,
    default: '',
  },
  progressText: {
    type: String,
    default: '正在生成图片',
  },
  pollHint: {
    type: String,
    default: '每 5 秒轮询任务状态',
  },
})

const emit = defineEmits([
  'update:current-task-title',
  'select-all-cards',
  'batch-download',
  'toggle-card',
  'download-card',
  'edit-card',
  'zoom-card',
  'delete-card',
  'create-new-task',
  'open-history',
])
</script>

<template>
  <GeneratorWorkspaceShell :content-class="outputCards.length > 0 || generating || creatingBatch ? 'p-6' : 'p-0'">
    <template #header>
      <div class="z-10 flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-6 shadow-sm backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <span class="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">{{ titleBadge }}</span>
          <input
            :value="currentTaskTitle"
            type="text"
            class="w-64 border-b border-transparent bg-transparent py-0.5 text-xs font-bold text-slate-800 transition-all hover:border-slate-300 focus:border-primary focus:outline-none"
            @input="emit('update:current-task-title', $event.target.value)"
          />
        </div>

        <div class="flex items-center gap-3">
          <template v-if="outputCards.length > 0">
            <slot name="toolbar-extra"></slot>
            <div class="flex items-center gap-2">
              <button type="button" class="text-xs font-semibold text-slate-500 hover:text-primary" @click="emit('select-all-cards', true)">全选</button>
              <span class="text-xs text-slate-300">/</span>
              <button type="button" class="text-xs font-semibold text-slate-500 hover:text-slate-700" @click="emit('select-all-cards', false)">全不选</button>
            </div>
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-xs font-bold text-white shadow-md transition-all hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="selectedCardsCount === 0 || downloading"
              @click="emit('batch-download')"
            >
              <RefreshCw v-if="downloading" class="h-3.5 w-3.5 animate-spin stroke-[2.5]" />
              <Download v-else class="h-3.5 w-3.5 stroke-[2.5]" />
              {{ downloading ? '打包中...' : `批量下载 (${selectedCardsCount}${mediaUnit})` }}
            </button>
            <div class="h-4 w-px bg-slate-200"></div>
          </template>
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-lg border border-primary/30 bg-white px-3 py-1.5 text-xs font-semibold text-primary transition-all hover:bg-primary/5"
            :disabled="generating"
            :class="{ 'cursor-not-allowed opacity-50': generating }"
            @click="emit('create-new-task')"
          >
            <Plus class="h-3.5 w-3.5 stroke-[2.5]" />
            新建任务
          </button>
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition-all hover:border-primary/40 hover:text-primary"
            @click="emit('open-history')"
          >
            <Clock3 class="h-3.5 w-3.5" />
            生成记录
          </button>
        </div>
      </div>
    </template>

    <template #default>
      <div v-if="creatingBatch && outputCards.length === 0" class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/95 p-8">
        <div class="w-full max-w-md space-y-6 text-center">
          <div class="relative mx-auto flex h-24 w-24 items-center justify-center">
            <div class="absolute inset-0 animate-ping rounded-full bg-primary/10"></div>
            <div class="absolute inset-2 animate-spin rounded-full border border-dashed border-primary/40"></div>
            <RefreshCw class="h-10 w-10 animate-pulse text-primary" />
          </div>
          <div class="space-y-2">
            <h4 class="text-base font-bold text-slate-800">{{ loadingTitle }}</h4>
            <p class="text-xs text-slate-500">
              <slot name="loading-description">
                <template v-if="loadingDescription">{{ loadingDescription }}</template>
                <template v-else>
                  正在按 <span class="font-semibold text-primary">{{ settings.platform }}</span> 和
                  <span class="font-semibold text-secondary">{{ selectedImageLabel }}</span> 输出{{ mediaType === 'video' ? '视频' : '图片' }}
                </template>
              </slot>
            </p>
          </div>
          <div class="h-28 space-y-1.5 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-3 text-left font-mono text-xs text-slate-500 shadow-inner">
            <div v-for="(log, idx) in genLogs" :key="idx" class="flex items-center gap-2">
              <span class="font-bold text-primary">▶</span>
              <span>{{ log }}</span>
            </div>
          </div>
          <p class="text-xs font-bold text-slate-400">正在创建任务 ...</p>
        </div>
      </div>

      <GeneratorPreviewShowcase
        v-if="outputCards.length === 0 && !generating && !creatingBatch"
        :title="emptyTitle"
        :subtitle="emptySubtitle"
        :slides="emptySlides"
        :media-type="mediaType"
      />

      <div v-else-if="outputCards.length > 0" class="space-y-4">
        <div v-if="generating" class="flex items-center justify-between rounded-xl border border-primary/20 bg-primary/5 px-4 py-2 text-xs">
          <div class="flex items-center gap-2 text-slate-700">
            <RefreshCw class="h-3.5 w-3.5 animate-spin text-primary" />
            <span>
              {{ progressText }}，进行中
              <span class="font-bold text-primary">{{ runningCount }}</span>
              {{ mediaUnit }}，已完成
              <span class="font-bold text-primary">{{ generatedCount }}</span>
              / {{ jobTotal || totalCount }}
              <template v-if="failedCount > 0">
                ，失败 <span class="font-bold text-rose-500">{{ failedCount }}</span> {{ mediaUnit }}
              </template>
            </span>
          </div>
          <span class="font-mono text-slate-400">{{ pollHint }}</span>
        </div>
        <VideoGeneratedCardGrid
          v-if="mediaType === 'video'"
          :cards="outputCards"
          :platform="settings.platform || settings.market || ''"
          :language="settings.language"
          :video-label="selectedImageLabel"
          :get-module-name="getModuleName"
          :downloading="downloading"
          @toggle-card="emit('toggle-card', $event)"
          @download-card="emit('download-card', $event)"
          @zoom-card="emit('zoom-card', $event)"
          @delete-card="emit('delete-card', $event)"
        />
        <AudioGeneratedCardGrid
          v-else-if="mediaType === 'audio'"
          :cards="outputCards"
          :downloading="downloading"
          @toggle-card="emit('toggle-card', $event)"
          @download-card="emit('download-card', $event)"
          @delete-card="emit('delete-card', $event)"
        />
        <GeneratedCardGrid
          v-else
          :cards="outputCards"
          :platform="settings.platform || settings.market || ''"
          :language="settings.language"
          :image-label="selectedImageLabel"
          :get-module-name="getModuleName"
          :downloading="downloading"
          @toggle-card="emit('toggle-card', $event)"
          @download-card="emit('download-card', $event)"
          @edit-card="emit('edit-card', $event)"
          @zoom-card="emit('zoom-card', $event)"
          @delete-card="emit('delete-card', $event)"
        />
      </div>

      <div v-if="outputCards.length === 0 && !generating && !creatingBatch && emptySlides.length === 0" class="flex h-full items-center justify-center text-slate-300">
        <ImageIcon class="h-8 w-8" />
      </div>
    </template>
  </GeneratorWorkspaceShell>
</template>
