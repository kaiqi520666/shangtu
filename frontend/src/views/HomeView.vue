<script setup>
import { computed } from 'vue'
import { ArrowRight } from 'lucide-vue-next'
import HomeFeatures from '@/components/home/HomeFeatures.vue'
import HomeHero from '@/components/home/HomeHero.vue'
import HomeShowcase from '@/components/home/HomeShowcase.vue'
import HomeWorkflow from '@/components/home/HomeWorkflow.vue'
import {
  featureItems,
  homeImages,
  showcaseItems,
  workflowItems,
} from '@/components/home/homeContent.js'
import { useAuthStore } from '@/stores/auth.js'

const authStore = useAuthStore()
const workspaceTarget = computed(() =>
  authStore.isAuthenticated
    ? '/generator/product-suite'
    : { path: '/login', query: { redirect: '/generator/product-suite' } },
)

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="min-h-screen scroll-smooth bg-slate-50 text-slate-950">
    <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
        <RouterLink to="/" class="flex items-center gap-3"
          ><span
            class="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/15 bg-white shadow-sm"
            ><img src="/logo.png" class="h-8 w-8 object-contain" alt="NodePass AI Logo" /></span
          ><span
            ><span class="block text-sm font-black text-slate-950">NodePass AI</span
            ><span class="block text-xs font-medium text-slate-500">电商内容生成平台</span></span
          ></RouterLink
        >
        <nav
          class="hidden items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-black text-slate-500 shadow-inner md:flex"
        >
          <a
            v-for="item in [
              { id: 'features', label: '能力矩阵' },
              { id: 'workflow', label: '生成流程' },
              { id: 'showcase', label: '作品展示' },
            ]"
            :key="item.id"
            :href="`#${item.id}`"
            class="rounded-full px-4 py-2 transition-colors hover:bg-white hover:text-primary hover:shadow-sm"
            @click.prevent="scrollToSection(item.id)"
            >{{ item.label }}</a
          >
        </nav>
        <div class="flex items-center gap-2">
          <RouterLink
            v-if="authStore.isAuthenticated"
            to="/generator/product-suite"
            class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-secondary"
            >进入工作台</RouterLink
          ><template v-else
            ><RouterLink
              to="/login"
              class="hidden rounded-xl px-4 py-2 text-xs font-bold text-slate-600 hover:text-primary sm:inline-flex"
              >登录</RouterLink
            ><RouterLink
              to="/register"
              class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-secondary"
              >注册</RouterLink
            ></template
          >
        </div>
      </div>
    </header>
    <main>
      <HomeHero :image="homeImages.hero" :workspace-target="workspaceTarget" />
      <HomeFeatures :items="featureItems" />
      <HomeWorkflow :items="workflowItems" />
      <HomeShowcase :items="showcaseItems" />
      <section class="bg-slate-950 px-5 py-14 text-white lg:px-8">
        <div
          class="mx-auto flex max-w-7xl flex-col justify-between gap-6 md:flex-row md:items-center"
        >
          <div>
            <h2 class="text-2xl font-black">开始生成你的下一批电商内容</h2>
            <p class="mt-2 text-sm text-slate-300">
              图片、视频、AI 配音、数字人与翻译能力已经在工作台内准备好。
            </p>
          </div>
          <RouterLink
            :to="workspaceTarget"
            class="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white shadow-lg hover:bg-secondary"
            >进入 NodePass AI<ArrowRight class="h-4 w-4"
          /></RouterLink>
        </div>
      </section>
    </main>
  </div>
</template>
