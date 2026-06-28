<script setup>
import { Sparkles } from 'lucide-vue-next'

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

    <main class="relative z-10 w-full max-w-[450px]">
      <section class="mb-6 text-center">
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
