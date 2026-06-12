<script setup>
import UserMenu from '@/components/layout/UserMenu.vue'
</script>

<template>
  <header class="z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-6 shadow-sm backdrop-blur-md">
    <div class="flex items-center gap-3">
      <div class="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/10 bg-white shadow-sm">
        <img src="/logo.png" class="h-8 w-8 object-contain" alt="NodePass AI Logo" />
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
      <div class="h-6 w-px bg-slate-200"></div>
      <UserMenu />
    </div>
  </header>
</template>
