<script setup>
import { AudioLines, Clapperboard, Film, Image, Images, Languages, PackageCheck, ShieldCheck, Sparkles, UserRoundCheck, WandSparkles } from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const mainNavs = [
  { name: '商品套图', desc: '白底图、场景图、卖点图、细节图一键成套', icon: PackageCheck, to: '/generator/product-suite' },
  { name: '商品详情图', desc: 'AI 批量详情图排版生成模块', icon: Image, to: '/generator/product-image' },
  { name: '商品视频', desc: '商品图一键生成电商短视频素材', icon: Clapperboard, to: '/generator/product-video' },
  { name: '数字人', desc: '系统数字人和系统声音生成口播视频', icon: UserRoundCheck, to: '/generator/digital-human' },
  { name: '视频翻译', desc: '上传视频并翻译为目标语言', icon: Languages, to: '/generator/video-translation' },
  { name: 'AI配音', desc: '预置音色生成 MP3 配音', icon: AudioLines, to: '/generator/voiceover' },
  { name: '服饰穿搭', desc: '真人模特试衣与穿搭场景生成模块', icon: WandSparkles, to: '/generator/outfit' },
  { name: '自由生图', desc: '输入提示词，自由生成或参考图片改图', icon: Sparkles, to: '/generator/free-image' },
  { name: '自由生视频', desc: '提示词、首帧图或参考图生成视频', icon: Film, to: '/generator/free-video' },
  { name: '资产库', desc: '管理所有已生成的图片资源', icon: Images, to: '/generator/assets' },
]

const route = useRoute()
const authStore = useAuthStore()

const adminNav = {
  name: '管理后台',
  desc: '用户、订单、积分流水和平台运营管理',
  icon: ShieldCheck,
  to: '/admin/overview',
  activeBase: '/admin',
}

function isNavActive(nav) {
  const currentPath = route.path.replace(/\/+$/, '') || '/'
  const navPath = (nav.activeBase || nav.to).replace(/\/+$/, '') || '/'

  return currentPath === navPath || currentPath.startsWith(`${navPath}/`)
}
</script>

<template>
  <aside class="flex w-16 flex-col items-center border-r border-slate-200 bg-slate-50 py-3">
    <div class="flex min-h-0 w-full flex-1 flex-col items-center gap-1 overflow-y-auto">
      <div v-for="nav in mainNavs" :key="nav.to" class="flex w-full justify-center">
        <RouterLink
          :to="nav.to"
          class="flex h-12 w-12 items-center justify-center rounded-xl transition-colors duration-200"
          :aria-label="nav.name"
          :title="`${nav.name}：${nav.desc}`"
          :class="isNavActive(nav) ? 'bg-primary/10 text-primary' : 'text-slate-500 hover:bg-white hover:text-primary'"
        >
          <component :is="nav.icon" class="h-5 w-5 stroke-[1.8]" />
        </RouterLink>
      </div>
      <template v-if="authStore.isSuperAdmin">
        <div class="flex w-full justify-center">
          <RouterLink
            :to="adminNav.to"
            class="flex h-12 w-12 items-center justify-center rounded-xl transition-colors duration-200"
            :aria-label="adminNav.name"
            :title="`${adminNav.name}：${adminNav.desc}`"
            :class="isNavActive(adminNav) ? 'bg-primary/10 text-primary' : 'text-slate-500 hover:bg-white hover:text-primary'"
          >
            <component :is="adminNav.icon" class="h-5 w-5 stroke-[1.8]" />
          </RouterLink>
        </div>
      </template>
    </div>
  </aside>
</template>
