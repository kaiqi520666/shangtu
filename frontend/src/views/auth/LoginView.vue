<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '@/api/auth.js'
import AuthForm from '@/components/auth/AuthForm.vue'
import AuthPageShell from '@/components/auth/AuthPageShell.vue'
import { useToast } from '@/composables/useToast.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()
const loading = ref(false)

onMounted(() => {
  if (route.query.loggedOut === '1') {
    toast.success('已退出登录')
    router.replace('/login')
  }
})

async function handleLogin(payload) {
  if (loading.value) return
  loading.value = true
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
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthPageShell>
    <AuthForm mode="login" :loading="loading" @submit="handleLogin" />
  </AuthPageShell>
</template>
