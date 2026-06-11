<script setup>
import { Download, PackageCheck, RefreshCw } from 'lucide-vue-next'
import GeneratedCardGrid from '@/components/GeneratedCardGrid.vue'
import GeneratorPreviewShowcase from '@/components/GeneratorPreviewShowcase.vue'
import GeneratorWorkspaceShell from '@/components/GeneratorWorkspaceShell.vue'
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
  getStructureStrategy: {
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
  'regenerate-card',
  'zoom-card',
])
</script>

<template>
  <GeneratorWorkspaceShell :content-class="outputCards.length > 0 || generating ? 'p-6' : 'p-0'">
    <template #header>
      <div class="z-10 flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-6 shadow-sm backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <span class="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">本次套图任务</span>
          <input
            :value="currentTaskTitle"
            type="text"
            class="w-64 border-b border-transparent bg-transparent py-0.5 text-xs font-bold text-slate-800 transition-all hover:border-slate-300 focus:border-primary focus:outline-none"
            @input="emit('update:current-task-title', $event.target.value)"
          />
        </div>

        <div v-if="outputCards.length > 0" class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <button type="button" class="text-xs font-semibold text-slate-500 hover:text-primary" @click="emit('select-all-cards', true)">全选</button>
            <span class="text-xs text-slate-300">/</span>
            <button type="button" class="text-xs font-semibold text-slate-500 hover:text-slate-700" @click="emit('select-all-cards', false)">全不选</button>
          </div>
          <div class="h-4 w-px bg-slate-200"></div>
          <button type="button" class="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-xs font-bold text-white shadow-md transition-all hover:bg-secondary" @click="emit('batch-download')">
            <Download class="h-3.5 w-3.5 stroke-[2.5]" />
            批量下载 ({{ selectedCardsCount }}张)
          </button>
        </div>
      </div>
    </template>

    <template #default>
      <div v-if="generating" class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/95 p-8">
        <div class="w-full max-w-md space-y-6 text-center">
          <div class="relative mx-auto flex h-24 w-24 items-center justify-center">
            <div class="absolute inset-0 animate-ping rounded-full bg-primary/10"></div>
            <div class="absolute inset-2 animate-spin rounded-full border border-dashed border-primary/40"></div>
            <RefreshCw class="h-10 w-10 animate-pulse text-primary" />
          </div>
          <div class="space-y-2">
            <h4 class="text-base font-bold text-slate-800">AI 商品套图生成中</h4>
            <p class="text-xs text-slate-500">
              正在按 <span class="font-semibold text-primary">{{ settings.platform }}</span> 和
              <span class="font-semibold text-secondary">{{ selectedImageLabel }}</span> 输出统一风格套图
            </p>
          </div>
          <div class="h-28 space-y-1.5 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-3 text-left font-mono text-xs text-slate-500 shadow-inner">
            <div v-for="(log, idx) in genLogs" :key="idx" class="flex items-center gap-2">
              <span class="font-bold text-primary">▶</span>
              <span>{{ log }}</span>
            </div>
          </div>
          <p class="text-xs font-bold text-slate-400">已生成 {{ generatedCount }} / {{ totalCount }}</p>
        </div>
      </div>

      <GeneratorPreviewShowcase
        v-if="outputCards.length === 0 && !generating"
        title="AI商品套图"
        subtitle="上传商品图，AI 即刻生成符合多电商平台规范的高转化率商品套图。"
        :slides="productSuitePreviewSlides"
      />

      <GeneratedCardGrid
        v-else-if="!generating"
        :cards="outputCards"
        :ratio="selectedImageLabel"
        :platform="settings.platform"
        :language="settings.language"
        :get-module-name="getStructureName"
        :get-module-strategy="getStructureStrategy"
        @toggle-card="emit('toggle-card', $event)"
        @download-card="emit('download-card', $event)"
        @regenerate-card="emit('regenerate-card', $event)"
        @zoom-card="emit('zoom-card', $event)"
      />

      <div v-if="outputCards.length === 0 && !generating && productSuitePreviewSlides.length === 0" class="flex h-full items-center justify-center text-slate-300">
        <PackageCheck class="h-8 w-8" />
      </div>
    </template>
  </GeneratorWorkspaceShell>
</template>
