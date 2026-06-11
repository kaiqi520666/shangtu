<script setup>
import { Boxes, Clock3, Layers } from 'lucide-vue-next'
import UserMenu from '@/components/UserMenu.vue'

defineProps({
  taskCount: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['open-queue', 'open-history'])
</script>

<template>
  <header class="z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-6 shadow-sm backdrop-blur-md">
    <div class="flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-primary to-secondary text-white shadow-lg shadow-primary/10">
        <Layers class="h-5 w-5 stroke-[2.5]" />
      </div>
      <div>
        <h1 class="flex items-center gap-2 text-base font-bold text-slate-800">
          NodePass AI
          <span class="rounded border border-primary/20 bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">SaaS Pro</span>
        </h1>
        <p class="text-xs text-slate-500">商品主图 AI 批量智能生成系统</p>
      </div>
    </div>

    <div class="flex items-center gap-6">
      <div class="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100 px-3 py-1.5">
        <span class="h-2 w-2 animate-pulse rounded-full bg-primary"></span>
        <span class="text-xs text-slate-500">额度剩余</span>
        <span class="text-xs font-bold text-primary">1,280 点</span>
      </div>
      <button type="button" class="relative flex items-center gap-1.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:text-primary" @click="emit('open-queue')">
        <Boxes class="h-4 w-4" />
        批量托管
        <span v-if="taskCount > 0" class="absolute -right-2 -top-1 flex h-4 w-4 animate-bounce items-center justify-center rounded-full bg-primary text-xs font-bold text-white">
          {{ taskCount }}
        </span>
      </button>
      <button type="button" class="flex items-center gap-1.5 text-xs font-medium text-slate-600 transition-colors hover:text-primary" @click="emit('open-history')">
        <Clock3 class="h-4 w-4" />
        生成记录
      </button>
      <div class="h-6 w-px bg-slate-200"></div>
      <UserMenu />
    </div>
  </header>
</template>
