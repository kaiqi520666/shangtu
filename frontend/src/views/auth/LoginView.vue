<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '@/api/auth.js'
import AuthForm from '@/components/auth/AuthForm.vue'
import { useToast } from '@/composables/useToast.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

onMounted(() => {
  if (route.query.loggedOut === '1') {
    toast.success('已退出登录')
    router.replace('/login')
  }
})

async function handleLogin(payload) {
  try {
    const result = await login({
      email: payload.email,
      password: payload.password,
    })

    if (result.code !== 0) {
      toast.error(result.message || '登录失败')
      return
    }

    authStore.login({
      email: result.data?.email || payload.email,
      username: result.data?.username,
      token: result.data?.token,
      userId: result.data?.user_id,
      credits: result.data?.credits,
    })
    toast.success('登录成功')
    router.push(typeof route.query.redirect === 'string' ? route.query.redirect : '/generator')
  } catch (error) {
    toast.error(error.response?.data?.message || '登录失败，请稍后重试')
  }
}
</script>

<template>
  <div class="grid min-h-screen bg-slate-50 lg:grid-cols-[1fr_480px]">
    <section class="hidden bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
      <div class="text-lg font-bold">NodePass AI</div>
      <div>
        <p class="max-w-xl text-4xl font-bold leading-tight">批量生成适配多平台的商品主图。</p>
        <p class="mt-4 max-w-lg text-sm leading-6 text-slate-300">用邮箱登录后进入工作台，上传商品图、选择平台和尺寸，一次生成完整电商视觉素材。</p>
      </div>
      <div class="text-xs text-slate-400">NodePass AI Generator</div>
    </section>
    <section class="flex items-center justify-center bg-white px-6 py-12">
      <AuthForm mode="login" @submit="handleLogin" />
    </section>
  </div>
</template>
