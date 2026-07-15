<script setup>
import { RefreshCw } from 'lucide-vue-next'
import GeneratedCardGrid from '@/components/generation/cards/GeneratedCardGrid.vue'
import GeneratorPreviewShowcase from '@/components/generation/workspace/GeneratorPreviewShowcase.vue'
import GeneratorWorkspaceShell from '@/components/generation/workspace/GeneratorWorkspaceShell.vue'
import GenerationWorkspaceHeader from '@/components/generation/workspace/GenerationWorkspaceHeader.vue'
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
  emptyImage: {
    type: String,
    default: '',
  },
  emptyImageAlt: {
    type: String,
    default: '',
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
  <GeneratorWorkspaceShell
    :content-class="outputCards.length > 0 || generating || creatingBatch ? 'p-4 sm:p-5' : 'p-0'"
  >
    <template #header>
      <GenerationWorkspaceHeader
        :title="currentTaskTitle"
        :title-badge="titleBadge"
        :has-cards="outputCards.length > 0"
        :selected-count="selectedCardsCount"
        :downloading="downloading"
        :generating="generating"
        :media-unit="mediaUnit"
        @update:title="emit('update:current-task-title', $event)"
        @select-all="emit('select-all-cards', $event)"
        @download="emit('batch-download')"
        @create="emit('create-new-task')"
        @history="emit('open-history')"
      >
        <template #extra><slot name="toolbar-extra"></slot></template>
      </GenerationWorkspaceHeader>
    </template>

    <template #default>
      <div
        v-if="creatingBatch && outputCards.length === 0"
        class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/95 p-6"
      >
        <div class="w-full max-w-sm space-y-3 text-center">
          <RefreshCw class="mx-auto h-6 w-6 animate-spin text-primary" />
          <div class="space-y-2">
            <h4 class="text-base font-bold text-slate-800">{{ loadingTitle }}</h4>
            <p class="text-xs text-slate-500">
              <slot name="loading-description">
                <template v-if="loadingDescription">{{ loadingDescription }}</template>
                <template v-else>
                  正在按 <span class="font-semibold text-primary">{{ settings.platform }}</span> 和
                  <span class="font-semibold text-secondary">{{ selectedImageLabel }}</span> 输出{{
                    mediaType === 'video' ? '视频' : '图片'
                  }}
                </template>
              </slot>
            </p>
          </div>
        </div>
      </div>

      <GeneratorPreviewShowcase
        v-if="outputCards.length === 0 && !generating && !creatingBatch"
        :title="emptyTitle"
        :subtitle="emptySubtitle"
        :slides="emptySlides"
        :image-url="emptyImage"
        :image-alt="emptyImageAlt"
        :media-type="mediaType"
      />

      <div v-else-if="outputCards.length > 0" class="space-y-4">
        <div
          v-if="generating"
          class="flex items-center rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-xs"
        >
          <div class="flex items-center gap-2 text-slate-700">
            <RefreshCw class="h-3.5 w-3.5 animate-spin text-primary" />
            <span>
              {{ progressText }}，进行中
              <span class="font-bold text-primary">{{ runningCount }}</span>
              {{ mediaUnit }}，已完成
              <span class="font-bold text-primary">{{ generatedCount }}</span>
              / {{ jobTotal || totalCount }}
              <template v-if="failedCount > 0">
                ，失败 <span class="font-bold text-rose-500">{{ failedCount }}</span>
                {{ mediaUnit }}
              </template>
            </span>
          </div>
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
    </template>
  </GeneratorWorkspaceShell>
</template>
