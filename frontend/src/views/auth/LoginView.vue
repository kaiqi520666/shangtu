<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCaptchaConfig, login } from '@/api/auth.js'
import AuthForm from '@/components/auth/AuthForm.vue'
import AuthPageShell from '@/components/auth/AuthPageShell.vue'
import { useToast } from '@/composables/useToast.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()
const loading = ref(false)
const captchaRequired = ref(false)
const captchaSiteKey = ref('')
const authForm = ref(null)

async function loadCaptchaConfig() {
  if (captchaSiteKey.value) return
  try {
    const result = await getCaptchaConfig()
    if (result.code === 0) captchaSiteKey.value = result.data?.site_key || ''
  } catch {
    toast.error('人机验证配置加载失败')
  }
}

onMounted(() => {
  if (route.query.loggedOut === '1') {
    toast.success('已退出登录')
    router.replace('/login')
  } else if (route.query.passwordChanged === '1') {
    toast.success('密码已修改，请重新登录')
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
      captcha_token: payload.captchaToken || undefined,
    })

    if (result.code !== 0) {
      if (result.data?.captcha_required) {
        captchaRequired.value = true
        await loadCaptchaConfig()
      }
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
    if (payload.captchaToken) authForm.value?.resetCaptcha()
  }
}
</script>

<template>
  <AuthPageShell>
    <AuthForm
      ref="authForm"
      mode="login"
      :loading="loading"
      :captcha-required="captchaRequired"
      :captcha-site-key="captchaSiteKey"
      captcha-action="login"
      @submit="handleLogin"
    />
  </AuthPageShell>
</template>
