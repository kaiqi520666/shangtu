<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDown, LogOut, Settings, UserRound, WalletCards } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()
const open = ref(false)
const root = ref(null)

const email = computed(() => authStore.user?.email || 'user@example.com')
const credits = computed(() => authStore.credits || 0)
const initials = computed(() => {
  const source = email.value.split('@')[0] || 'VIP'
  return source.slice(0, 2).toUpperCase()
})

function handleLogout() {
  authStore.logout()
  open.value = false
  router.push({ path: '/login', query: { loggedOut: '1' } })
}

function handleClickOutside(event) {
  if (root.value && !root.value.contains(event.target)) {
    open.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-1.5 py-1 text-slate-700 shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5"
      @click.stop="open = !open"
    >
      <span class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-primary to-secondary text-xs font-bold text-white shadow-sm">
        {{ initials }}
      </span>
      <ChevronDown class="mr-1 h-3.5 w-3.5 text-slate-400 transition-transform" :class="open ? 'rotate-180 text-primary' : ''" />
    </button>

    <div v-if="open" class="absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      <div class="border-b border-slate-100 p-4">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-sm font-bold text-primary">
            {{ initials }}
          </span>
          <div class="min-w-0">
            <p class="truncate text-sm font-bold text-slate-800">{{ email }}</p>
            <p class="text-xs text-slate-400">NodePass AI · SaaS Pro</p>
          </div>
        </div>
      </div>

      <div class="p-2">
        <button type="button" class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-xs font-medium text-slate-600 hover:bg-slate-50">
          <WalletCards class="h-4 w-4 text-primary" />
          额度剩余：{{ credits }} 点
        </button>
        <button type="button" class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-xs font-medium text-slate-600 hover:bg-slate-50">
          <Settings class="h-4 w-4 text-slate-400" />
          账号设置
        </button>
        <button type="button" class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-xs font-medium text-slate-600 hover:bg-slate-50">
          <UserRound class="h-4 w-4 text-slate-400" />
          个人资料
        </button>
      </div>

      <div class="border-t border-slate-100 p-2">
        <button type="button" class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-xs font-bold text-rose-600 hover:bg-rose-50" @click="handleLogout">
          <LogOut class="h-4 w-4" />
          退出登录
        </button>
      </div>
    </div>
  </div>
</template>
