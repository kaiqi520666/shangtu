<script setup>
import { ImagePlus, RefreshCw } from 'lucide-vue-next'
import GeneratedCardGrid from '@/components/GeneratedCardGrid.vue'
import GeneratorPreviewShowcase from '@/components/GeneratorPreviewShowcase.vue'
import GeneratorWorkspaceShell from '@/components/GeneratorWorkspaceShell.vue'

defineProps({
  currentTaskTitle: {
    type: String,
    required: true,
  },
  previewSlides: {
    type: Array,
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
  selectedPoseCount: {
    type: Number,
    default: 0,
  },
  genLogs: {
    type: Array,
    required: true,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  settings: {
    type: Object,
    required: true,
  },
  getPoseName: {
    type: Function,
    required: true,
  },
  getPoseStrategy: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'update:current-task-title',
  'select-all-cards',
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
          <span class="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">本次穿搭任务</span>
          <input
            :value="currentTaskTitle"
            type="text"
            class="w-64 border-b border-transparent bg-transparent py-0.5 text-xs font-bold text-slate-800 transition-all hover:border-slate-300 focus:border-primary focus:outline-none"
            @input="emit('update:current-task-title', $event.target.value)"
          />
        </div>

        <div v-if="outputCards.length > 0" class="flex items-center gap-2">
          <button type="button" class="text-xs font-semibold text-slate-500 hover:text-primary" @click="emit('select-all-cards', true)">全选</button>
          <span class="text-xs text-slate-300">/</span>
          <button type="button" class="text-xs font-semibold text-slate-500 hover:text-slate-700" @click="emit('select-all-cards', false)">全不选</button>
        </div>
      </div>
    </template>

    <div v-if="generating" class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/95 p-8">
      <div class="w-full max-w-md space-y-6 text-center">
        <div class="relative mx-auto flex h-24 w-24 items-center justify-center">
          <div class="absolute inset-0 animate-ping rounded-full bg-primary/10"></div>
          <div class="absolute inset-2 animate-spin rounded-full border border-dashed border-primary/40"></div>
          <RefreshCw class="h-10 w-10 animate-pulse text-primary" />
        </div>
        <div class="space-y-2">
          <h4 class="text-base font-bold text-slate-800">AI 服饰穿搭生成中</h4>
          <p class="text-xs text-slate-500">
            正在基于模特、场景和 <span class="font-semibold text-primary">{{ selectedImageLabel }}</span> 输出穿搭图
          </p>
        </div>
        <div class="h-28 space-y-1.5 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-3 text-left font-mono text-xs text-slate-500 shadow-inner">
          <div v-for="(log, idx) in genLogs" :key="idx" class="flex items-center gap-2">
            <span class="font-bold text-primary">▶</span>
            <span>{{ log }}</span>
          </div>
        </div>
        <p class="text-xs font-bold text-slate-400">已生成 {{ generatedCount }} / {{ selectedPoseCount }}</p>
      </div>
    </div>

    <GeneratorPreviewShowcase
      v-if="outputCards.length === 0 && !generating"
      title="AI服饰穿戴"
      subtitle="上传服装，选定模特，同场景多姿势套图即刻生成。"
      :slides="previewSlides"
    />

    <GeneratedCardGrid
      v-else-if="!generating"
      :cards="outputCards"
      :ratio="selectedImageLabel"
      :platform="settings.platform"
      :language="settings.language"
      :get-module-name="getPoseName"
      :get-module-strategy="getPoseStrategy"
      @toggle-card="emit('toggle-card', $event)"
      @download-card="emit('download-card', $event)"
      @regenerate-card="emit('regenerate-card', $event)"
      @zoom-card="emit('zoom-card', $event)"
    />

    <div v-if="outputCards.length === 0 && !generating && previewSlides.length === 0" class="flex h-full items-center justify-center text-slate-300">
      <ImagePlus class="h-8 w-8" />
    </div>
  </GeneratorWorkspaceShell>
</template>
