<script setup>
import GenerationWorkspace from '@/components/generation/GenerationWorkspace.vue'
import { productDetailPreviewSlides } from '@/constants/generator.js'

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
  getModuleName: {
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
    :get-module-name="getModuleName"
    title-badge="本次详情图任务"
    empty-title="商品详情图"
    empty-subtitle="上传商品图，生成策略后输出多张电商详情页模块图。"
    :empty-slides="productDetailPreviewSlides"
    loading-title="AI 商品详情图生成中"
    progress-text="正在生成商品详情图"
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
