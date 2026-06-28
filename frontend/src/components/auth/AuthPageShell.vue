<script setup>
import { ImagePlus, Layers3, ShieldCheck, Sparkles } from 'lucide-vue-next'

defineProps({
  headline: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
})

const signals = [
  { icon: ImagePlus, label: '商品图', value: '套图 / 详情' },
  { icon: Sparkles, label: '生成流', value: '策略 / 直出' },
  { icon: Layers3, label: '资产库', value: '统一沉淀' },
]
</script>

<template>
  <div
    class="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f6f8fb] px-5 py-10 text-slate-900 [background-image:linear-gradient(90deg,rgba(15,23,42,0.04)_1px,transparent_1px),linear-gradient(180deg,rgba(15,23,42,0.04)_1px,transparent_1px)] [background-size:44px_44px]"
  >
    <div class="absolute inset-x-0 top-0 h-28 bg-linear-to-b from-white to-transparent"></div>
    <div class="absolute inset-x-0 bottom-0 h-28 bg-linear-to-t from-white to-transparent"></div>

    <header class="absolute left-6 top-5 flex items-center gap-3 sm:left-8 sm:top-7">
      <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-primary shadow-lg shadow-slate-900/10">
        <Sparkles class="h-4 w-4" />
      </div>
      <div>
        <p class="text-sm font-black text-slate-900">商图 AI</p>
        <p class="text-[11px] font-semibold text-slate-400">Commerce Visual Studio</p>
      </div>
    </header>

    <aside
      class="pointer-events-none absolute left-8 top-1/2 hidden w-64 -translate-y-1/2 rounded-2xl border border-white/70 bg-white/70 p-5 shadow-2xl shadow-slate-900/8 backdrop-blur-xl xl:block"
    >
      <div class="mb-5 flex items-center gap-2 text-xs font-bold text-primary">
        <ShieldCheck class="h-4 w-4" />
        专业内容生产台
      </div>
      <h2 class="text-xl font-black leading-tight text-slate-950">{{ headline }}</h2>
      <p class="mt-3 text-xs leading-6 text-slate-500">{{ description }}</p>
    </aside>

    <aside class="pointer-events-none absolute right-8 top-1/2 hidden w-56 -translate-y-1/2 space-y-3 xl:block">
      <div
        v-for="signal in signals"
        :key="signal.label"
        class="flex items-center gap-3 rounded-2xl border border-white/70 bg-white/70 p-4 shadow-xl shadow-slate-900/7 backdrop-blur-xl"
      >
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-primary">
          <component :is="signal.icon" class="h-4 w-4" />
        </div>
        <div>
          <p class="text-xs font-bold text-slate-400">{{ signal.label }}</p>
          <p class="mt-0.5 text-sm font-black text-slate-900">{{ signal.value }}</p>
        </div>
      </div>
    </aside>

    <main class="relative z-10 w-full max-w-[450px]">
      <section class="mb-6 text-center xl:hidden">
        <h1 class="text-2xl font-black tracking-normal text-slate-950">{{ headline }}</h1>
        <p class="mx-auto mt-3 max-w-sm text-sm leading-6 text-slate-500">{{ description }}</p>
      </section>

      <section class="rounded-[28px] border border-white/80 bg-white/90 p-6 shadow-2xl shadow-slate-900/12 backdrop-blur-xl sm:p-8">
        <slot />
      </section>

      <p class="mt-5 text-center text-xs font-semibold text-slate-400">
        商品视觉、视频素材与资产管理的一体化工作台
      </p>
    </main>
  </div>
</template>
