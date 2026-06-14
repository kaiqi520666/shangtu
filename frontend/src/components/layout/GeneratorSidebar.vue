<script setup>
import { HelpCircle, Image, Images, PackageCheck, Sparkles, WandSparkles } from 'lucide-vue-next'
import { useRoute } from 'vue-router'

const mainNavs = [
  { name: '商品套图', desc: '白底图、场景图、卖点图、细节图一键成套', icon: PackageCheck, to: '/generator/product-suite' },
  { name: '商品详情图', desc: 'AI 批量详情图排版生成模块', icon: Image, to: '/generator/product-image' },
  { name: '服饰穿搭', desc: '真人模特试衣与穿搭场景生成模块', icon: WandSparkles, to: '/generator/outfit' },
  { name: '自由生图', desc: '输入提示词，自由生成或参考图片改图', icon: Sparkles, to: '/generator/free-image' },
  { name: '资产库', desc: '管理所有已生成的图片资源', icon: Images, to: '/generator/assets' },
]

const route = useRoute()

function isNavActive(nav) {
  const currentPath = route.path.replace(/\/+$/, '') || '/'
  const navPath = nav.to.replace(/\/+$/, '') || '/'

  return currentPath === navPath || currentPath.startsWith(`${navPath}/`)
}
</script>

<template>
  <aside class="flex w-20 flex-col items-center gap-6 border-r border-slate-200 bg-slate-100/50 py-4">
    <div class="flex w-full flex-col items-center gap-3">
      <div v-for="nav in mainNavs" :key="nav.to" class="group relative flex w-full flex-col items-center">
        <RouterLink
          :to="nav.to"
          class="relative flex h-11 w-11 items-center justify-center rounded-xl transition-all duration-300"
          :aria-label="nav.name"
          :class="isNavActive(nav) ? 'border border-primary/20 bg-primary/10 text-primary shadow-sm' : 'text-slate-500 hover:bg-white hover:text-slate-800 hover:shadow-sm'"
        >
          <span v-if="isNavActive(nav)" class="absolute -left-[15px] top-1/2 h-7 w-1 -translate-y-1/2 rounded-r-full bg-primary"></span>
          <component :is="nav.icon" class="h-5 w-5 stroke-[2.2]" />
        </RouterLink>
        <span class="mt-1 max-w-[64px] truncate text-center text-xs font-medium leading-none" :class="isNavActive(nav) ? 'text-primary' : 'text-slate-500'" :title="nav.name">
          {{ nav.name }}
        </span>
        <span class="pointer-events-none absolute left-[76px] top-1 z-50 whitespace-nowrap rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-800 opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
          {{ nav.desc }}
        </span>
      </div>
    </div>
    <div class="flex-1"></div>
    <button type="button" class="rounded-lg p-2 text-slate-400 transition-colors hover:text-slate-600">
      <HelpCircle class="h-5 w-5" />
    </button>
  </aside>
</template>
