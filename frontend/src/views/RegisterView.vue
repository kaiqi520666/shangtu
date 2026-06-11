<script setup>
import { useRouter } from 'vue-router'
import { register } from '@/api/auth.js'
import AuthForm from '@/components/AuthForm.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useToast } from '@/composables/useToast.js'

const router = useRouter()
const auth = useAuth()
const toast = useToast()

async function handleRegister(payload) {
  try {
    const result = await register({
      username: payload.username,
      email: payload.email,
      password: payload.password,
    })

    if (result.code !== 0) {
      toast.error(result.message || '注册失败')
      return
    }

    auth.login({
      username: payload.username,
      email: payload.email,
      token: result.data?.token,
      userId: result.data?.user_id,
    })
    toast.success('注册成功')
    router.push('/generator')
  } catch (error) {
    toast.error(error.response?.data?.message || '注册失败，请稍后重试')
  }
}
</script>

<template>
  <div class="grid min-h-screen bg-slate-50 lg:grid-cols-[1fr_480px]">
    <section class="hidden bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
      <div class="text-lg font-bold">NodePass AI</div>
      <div>
        <p class="max-w-xl text-4xl font-bold leading-tight">创建账号，开始搭建你的商品主图流水线。</p>
        <p class="mt-4 max-w-lg text-sm leading-6 text-slate-300">注册后即可进入生成工作台。当前为前端表单演示，后续可接入真实邮箱注册接口。</p>
      </div>
      <div class="text-xs text-slate-400">NodePass AI Generator</div>
    </section>
    <section class="flex items-center justify-center bg-white px-6 py-12">
      <AuthForm mode="register" @submit="handleRegister" />
    </section>
  </div>
</template>
