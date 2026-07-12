<script setup>
import { ArrowRight } from 'lucide-vue-next'
defineProps({ items: { type: Array, required: true } })
</script>

<template>
  <section id="features" class="mx-auto max-w-7xl scroll-mt-24 px-5 py-16 lg:px-8">
    <div class="mb-8 max-w-3xl">
      <p class="text-xs font-black uppercase text-primary">Creative Workspace</p>
      <h2 class="mt-2 text-2xl font-black text-slate-950 md:text-3xl">覆盖电商内容生产全链路</h2>
      <p class="mt-4 text-sm leading-7 text-slate-500">
        从素材上传到成品下载，功能入口集中在一个工作台，适合跨境电商、国内电商和短视频带货团队。
      </p>
    </div>
    <div class="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
      <RouterLink
        :to="items[0].to"
        class="group relative min-h-[460px] overflow-hidden rounded-3xl bg-slate-950 p-6 text-white shadow-xl"
      >
        <img
          :src="items[0].image"
          class="absolute inset-0 h-full w-full object-cover opacity-60 transition-transform duration-700 group-hover:scale-[1.04]"
          :alt="items[0].title"
        />
        <div class="absolute inset-0 bg-slate-950/45"></div>
        <div class="relative flex h-full flex-col justify-between">
          <div class="flex items-center justify-between">
            <span
              class="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-black backdrop-blur"
              >核心能力</span
            ><span
              class="flex h-10 w-10 items-center justify-center rounded-full bg-white/15 backdrop-blur group-hover:bg-primary"
              ><ArrowRight class="h-5 w-5"
            /></span>
          </div>
          <div>
            <component :is="items[0].icon" class="mb-5 h-10 w-10 text-primary" />
            <h3 class="text-3xl font-black">{{ items[0].title }}</h3>
            <p class="mt-3 max-w-md text-sm leading-7 text-slate-100">{{ items[0].desc }}</p>
          </div>
        </div>
      </RouterLink>
      <div class="grid gap-4 sm:grid-cols-2">
        <RouterLink
          v-for="item in items.slice(1)"
          :key="item.title"
          :to="item.to"
          class="group rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-1 hover:border-primary/35 hover:shadow-md"
        >
          <div class="flex items-start justify-between gap-4">
            <span
              class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary"
              ><component :is="item.icon" class="h-6 w-6" /></span
            ><ArrowRight class="h-4 w-4 text-slate-300 group-hover:text-primary" />
          </div>
          <h3 class="mt-6 text-base font-black text-slate-950">{{ item.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-slate-500">{{ item.desc }}</p>
        </RouterLink>
      </div>
    </div>
  </section>
</template>
