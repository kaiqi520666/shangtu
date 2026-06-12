<script setup>
import { Download, RefreshCw, Upload } from 'lucide-vue-next'
import GeneratedCardGrid from '@/components/generation/GeneratedCardGrid.vue'
import GeneratorPreviewShowcase from '@/components/generation/GeneratorPreviewShowcase.vue'
import GeneratorWorkspaceShell from '@/components/generation/GeneratorWorkspaceShell.vue'
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
  selectedModules: {
    type: Array,
    required: true,
  },
  genLogs: {
    type: Array,
    required: true,
  },
  selectedCardsCount: {
    type: Number,
    default: 0,
  },
  generationProgressClass: {
    type: String,
    required: true,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  getModuleName: {
    type: Function,
    required: true,
  },
  getModuleStrategy: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'update:currentTaskTitle',
  'select-all-cards',
  'preview-long-image',
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
          <span class="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">本次详情图任务</span>
          <input
            :value="currentTaskTitle"
            type="text"
            class="w-64 border-b border-transparent bg-transparent py-0.5 text-xs font-bold text-slate-800 transition-all hover:border-slate-300 focus:border-primary focus:outline-none"
            @input="emit('update:currentTaskTitle', $event.target.value)"
          />
        </div>

        <div v-if="outputCards.length > 0" class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <button type="button" class="text-xs font-semibold text-slate-500 hover:text-primary" @click="emit('select-all-cards', true)">全选</button>
            <span class="text-xs text-slate-300">/</span>
            <button type="button" class="text-xs font-semibold text-slate-500 hover:text-slate-700" @click="emit('select-all-cards', false)">全不选</button>
          </div>
          <div class="h-4 w-px bg-slate-200"></div>
          <button type="button" class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50" @click="emit('preview-long-image')">
            <Upload class="h-3.5 w-3.5 text-slate-500" />
            长图拼接预览
          </button>
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
            <h4 class="text-base font-bold text-slate-800">AI 批量电商排版渲染引擎就绪</h4>
            <p class="text-xs text-slate-500">正在应用 <span class="font-semibold text-primary">[{{ settings.platform }}]</span> 的平台策略与 <span class="font-semibold text-secondary">[{{ selectedImageLabel }}]</span> 画布标准渲染高点击主图</p>
          </div>
          <div class="overflow-hidden rounded-full border border-slate-200 bg-slate-100">
            <div class="h-2 rounded-full bg-gradient-to-r from-primary to-secondary transition-all duration-300" :class="generationProgressClass"></div>
          </div>
          <div class="flex justify-between text-xs font-bold text-slate-400">
            <span>已生成 {{ generatedCount }} / {{ selectedModules.length }}</span>
            <span>预计耗时 1~2 秒</span>
          </div>
          <div class="h-28 space-y-1.5 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-3 text-left font-mono text-xs text-slate-500 shadow-inner">
            <div v-for="(log, idx) in genLogs" :key="idx" class="flex items-center gap-2">
              <span class="font-bold text-primary">▶</span>
              <span>{{ log }}</span>
            </div>
          </div>
        </div>
      </div>

      <GeneratorPreviewShowcase
        v-if="outputCards.length === 0 && !generating"
        title="商品详情图"
        subtitle="上传商品图，填写卖点要求，一键生成多类型电商详情图。"
        :slides="productDetailPreviewSlides"
      />

      <GeneratedCardGrid
        v-else-if="!generating"
        :cards="outputCards"
        :ratio="selectedImageLabel"
        :platform="settings.platform"
        :language="settings.language"
        :get-module-name="getModuleName"
        :get-module-strategy="getModuleStrategy"
        @toggle-card="emit('toggle-card', $event)"
        @download-card="emit('download-card', $event)"
        @regenerate-card="emit('regenerate-card', $event)"
        @zoom-card="emit('zoom-card', $event)"
      />
    </template>
  </GeneratorWorkspaceShell>
</template>
