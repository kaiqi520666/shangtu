<script setup>
defineProps({ items: { type: Array, required: true } })
</script>

<template>
  <section id="workflow" class="scroll-mt-24 border-y border-slate-200 bg-white">
    <div class="mx-auto max-w-7xl px-5 py-16 lg:px-8">
      <div class="mx-auto max-w-3xl text-center">
        <p class="text-xs font-black uppercase text-primary">Workflow</p>
        <h2 class="mt-2 text-2xl font-black text-slate-950 md:text-3xl">
          从素材到成品，一条线完成
        </h2>
        <p class="mt-4 text-sm leading-7 text-slate-500">
          把上传、选择、生成和资产沉淀串成固定流程，减少重复配置，让团队更快拿到可用内容。
        </p>
      </div>
      <div class="relative mt-10 grid gap-4 lg:grid-cols-4">
        <div class="absolute left-10 right-10 top-12 hidden h-px bg-primary/30 lg:block"></div>
        <article
          v-for="(item, index) in items"
          :key="item.title"
          class="relative rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-sm"
        >
          <div class="mb-6 flex items-center justify-between">
            <span
              class="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/20"
              ><component :is="item.icon" class="h-6 w-6" /></span
            ><span class="font-mono text-3xl font-black text-slate-200">0{{ index + 1 }}</span>
          </div>
          <h3 class="text-base font-black text-slate-950">{{ item.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-slate-500">{{ item.desc }}</p>
        </article>
      </div>
    </div>
  </section>
</template>
