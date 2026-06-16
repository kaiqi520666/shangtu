<script setup>
import UserMenu from '@/components/layout/UserMenu.vue'
import { useRechargeModal } from '@/composables/useRechargeModal.js'
import { useAuthStore } from '@/stores/auth.js'

const authStore = useAuthStore()
const { openRechargeModal } = useRechargeModal()
</script>

<template>
  <header class="z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-6 shadow-sm backdrop-blur-md">
    <div class="flex items-center gap-3">
      <div class="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/10 bg-white shadow-sm">
        <img src="/logo.png" class="h-8 w-8 object-contain" alt="商图 AI Logo" />
      </div>
      <div>
        <h1 class="flex items-center gap-2 text-base font-bold text-slate-800">
          商图 AI
          <span class="rounded border border-primary/20 bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">SaaS Pro</span>
        </h1>
        <p class="text-xs text-slate-500">商品主图 AI 批量智能生成系统</p>
      </div>
    </div>

    <div class="flex items-center gap-6">
      <div class="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100 px-3 py-1.5">
        <span class="h-2 w-2 animate-pulse rounded-full bg-primary"></span>
        <span class="text-xs text-slate-500">额度剩余</span>
        <span class="text-xs font-bold text-primary">{{ authStore.credits }} 点</span>
        <button type="button" class="rounded-full bg-primary px-2 py-0.5 text-xs font-bold text-white transition-colors hover:bg-primary/90" @click="openRechargeModal">
          充值
        </button>
      </div>
      <div class="h-6 w-px bg-slate-200"></div>
      <UserMenu />
    </div>
  </header>
</template>
