<script setup>
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import { productSuitePreviewSlides } from '@/constants/productSuite.js'

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
  generatedCount: {
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
  selectedImageLabel: {
    type: String,
    required: true,
  },
  getStructureName: {
    type: Function,
    required: true,
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
  <GenerationWorkspace
    :settings="settings"
    :current-task-title="currentTaskTitle"
    :output-cards="outputCards"
    :generating="generating"
    :generated-count="generatedCount"
    :total-count="totalCount"
    :job-total="jobTotal"
    :gen-logs="genLogs"
    :selected-cards-count="selectedCardsCount"
    :selected-image-label="selectedImageLabel"
    :get-module-name="getStructureName"
    title-badge="本次套图任务"
    empty-title="AI商品套图"
    empty-subtitle="上传商品图，AI 即刻生成符合多电商平台规范的高转化率商品套图。"
    :empty-slides="productSuitePreviewSlides"
    loading-title="AI 商品套图生成中"
    progress-text="正在生成商品套图"
    @update:current-task-title="emit('update:current-task-title', $event)"
    @select-all-cards="emit('select-all-cards', $event)"
    @batch-download="emit('batch-download')"
    @toggle-card="emit('toggle-card', $event)"
    @download-card="emit('download-card', $event)"
    @edit-card="emit('edit-card', $event)"
    @zoom-card="emit('zoom-card', $event)"
    @delete-card="emit('delete-card', $event)"
    @create-new-task="emit('create-new-task')"
    @open-history="emit('open-history')"
  />
</template>
