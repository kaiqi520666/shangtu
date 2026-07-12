<script setup>
import { ArrowRight } from 'lucide-vue-next'
defineProps({ items: { type: Array, required: true } })
</script>

<template>
  <section id="showcase" class="mx-auto max-w-7xl scroll-mt-24 px-5 py-16 lg:px-8">
    <div class="mb-8">
      <p class="text-xs font-black uppercase text-primary">Showcase</p>
      <h2 class="mt-2 text-2xl font-black text-slate-950 md:text-3xl">
        面向真实电商场景的视觉输出
      </h2>
    </div>
    <div class="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
      <article class="group overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div class="relative">
          <img
            :src="items[0].image"
            class="aspect-[16/10] w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            :alt="items[0].title"
          />
          <div
            class="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-xs font-black text-primary shadow-sm backdrop-blur"
          >
            图片生产
          </div>
        </div>
        <div class="flex flex-col gap-4 p-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 class="text-xl font-black text-slate-950">{{ items[0].title }}</h3>
            <p class="mt-2 text-sm leading-6 text-slate-500">{{ items[0].desc }}</p>
          </div>
          <RouterLink
            to="/generator/product-suite"
            class="inline-flex shrink-0 items-center gap-2 rounded-xl bg-primary px-4 py-2 text-xs font-black text-white hover:bg-secondary"
            >生成图片<ArrowRight class="h-4 w-4"
          /></RouterLink>
        </div>
      </article>
      <div class="grid gap-5">
        <article
          v-for="(item, index) in items.slice(1, 3)"
          :key="item.title"
          class="group grid overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm sm:grid-cols-2"
        >
          <img
            v-if="index === 0"
            :src="item.image"
            class="h-full min-h-56 w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            :alt="item.title"
          />
          <div class="flex flex-col justify-between p-5">
            <span
              class="w-fit rounded-full bg-primary/10 px-3 py-1 text-xs font-black text-primary"
              >{{ index === 0 ? '服饰穿搭' : '视频生成' }}</span
            >
            <div class="mt-8">
              <h3 class="text-lg font-black text-slate-950">{{ item.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-500">{{ item.desc }}</p>
            </div>
          </div>
          <img
            v-if="index === 1"
            :src="item.image"
            class="h-full min-h-56 w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            :alt="item.title"
          />
        </article>
      </div>
    </div>
    <article
      class="mt-5 grid overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm lg:grid-cols-[0.85fr_1.15fr]"
    >
      <div class="flex flex-col justify-center p-6">
        <span class="w-fit rounded-full bg-primary/10 px-3 py-1 text-xs font-black text-primary"
          >声音与全球化内容</span
        >
        <h3 class="mt-6 text-2xl font-black text-slate-950">{{ items[3].title }}</h3>
        <p class="mt-3 max-w-xl text-sm leading-7 text-slate-500">{{ items[3].desc }}</p>
        <div class="mt-5 flex flex-wrap gap-2">
          <RouterLink
            v-for="action in items[3].actions"
            :key="action.title"
            :to="action.to"
            class="group inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
            ><component :is="action.icon" class="h-4 w-4" />{{ action.title
            }}<ArrowRight class="h-3.5 w-3.5 text-slate-300 group-hover:text-primary"
          /></RouterLink>
        </div>
      </div>
      <img
        :src="items[3].image"
        class="h-full min-h-72 w-full object-cover"
        :alt="items[3].title"
      />
    </article>
  </section>
</template>
