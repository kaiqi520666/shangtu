<script setup>
import { ArrowRight, CheckCircle2, WandSparkles } from 'lucide-vue-next'
defineProps({
  image: { type: String, required: true },
  workspaceTarget: { type: [String, Object], required: true },
})
</script>

<template>
  <section class="relative overflow-hidden bg-slate-950">
    <img
      :src="image"
      class="absolute inset-0 h-full w-full object-cover opacity-70"
      alt="NodePass AI 电商内容生成主视觉"
    />
    <div class="absolute inset-0 bg-slate-950/55"></div>
    <div class="relative mx-auto flex min-h-[78vh] max-w-7xl items-center px-5 py-20 lg:px-8">
      <div class="max-w-3xl text-white">
        <p
          class="mb-5 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold backdrop-blur"
        >
          <WandSparkles class="h-4 w-4 text-primary" />AI 电商内容生成平台
        </p>
        <h1 class="text-4xl font-black leading-tight md:text-6xl">电商内容，一站生成</h1>
        <p class="mt-5 max-w-2xl text-base leading-8 text-slate-100 md:text-lg">
          商品图、详情页、短视频、AI 配音、数字人和视频翻译，统一在一个工作台完成。
        </p>
        <div class="mt-8 flex flex-wrap items-center gap-3">
          <RouterLink
            :to="workspaceTarget"
            class="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white shadow-lg hover:bg-secondary"
            >开始创作<ArrowRight class="h-4 w-4"
          /></RouterLink>
          <RouterLink
            to="/generator/assets"
            class="inline-flex items-center gap-2 rounded-xl border border-white/25 bg-white/10 px-5 py-3 text-sm font-bold text-white backdrop-blur hover:bg-white/20"
            >查看资产库</RouterLink
          >
        </div>
        <div class="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
          <div
            v-for="item in [
              ['图文视频', '覆盖商品图、短视频与详情内容'],
              ['资产复用', '上传素材与生成结果统一沉淀'],
              ['多语言扩展', '支持跨境内容翻译和本地化'],
            ]"
            :key="item[0]"
            class="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur"
          >
            <CheckCircle2 class="mb-3 h-5 w-5 text-primary" />
            <p class="text-lg font-black text-white">{{ item[0] }}</p>
            <p class="mt-1 text-xs leading-5 text-slate-200">{{ item[1] }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
