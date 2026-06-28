<script setup>
import { computed, reactive, ref } from 'vue'
import { Eye, EyeOff, LoaderCircle, Lock, Mail, UserRound } from 'lucide-vue-next'

const props = defineProps({
  mode: {
    type: String,
    required: true,
    validator: (value) => ['login', 'register'].includes(value),
  },
})

const emit = defineEmits(['submit'])

const form = reactive({
  username: '',
  email: '',
  password: '',
})
const showPassword = ref(false)
const loading = ref(false)
const message = ref('')

const isRegister = computed(() => props.mode === 'register')
const title = computed(() => (isRegister.value ? '创建账号' : '欢迎回来'))
const subtitle = computed(() => (isRegister.value ? '开通你的商图 AI 工作台' : '登录后继续你的内容生产任务'))
const buttonText = computed(() => (isRegister.value ? '创建账号' : '进入工作台'))

async function handleSubmit() {
  message.value = ''

  if (isRegister.value && !form.username.trim()) {
    message.value = '请输入用户名'
    return
  }

  if (!form.email.trim() || !form.password) {
    message.value = '请输入邮箱和密码'
    return
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    message.value = '请输入有效邮箱'
    return
  }

  if (form.password.length < 6) {
    message.value = '密码至少 6 位'
    return
  }

  loading.value = true
  await new Promise((resolve) => {
    window.setTimeout(resolve, 450)
  })
  loading.value = false
  emit('submit', { ...form })
}
</script>

<template>
  <div class="w-full">
    <div class="mb-7 text-center">
      <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-primary shadow-lg shadow-slate-950/15">
        <Lock class="h-5 w-5" />
      </div>
      <h1 class="text-2xl font-black tracking-normal text-slate-950">{{ title }}</h1>
      <p class="mt-2 text-sm font-medium text-slate-500">{{ subtitle }}</p>
    </div>

    <form class="space-y-4" @submit.prevent="handleSubmit">
      <label v-if="isRegister" class="block">
        <span class="mb-1.5 block text-xs font-bold text-slate-500">用户名</span>
        <span class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50/80 px-3 transition-colors focus-within:border-primary focus-within:bg-white focus-within:ring-2 focus-within:ring-primary/15">
          <UserRound class="h-4 w-4 text-slate-400" />
          <input
            v-model="form.username"
            type="text"
            autocomplete="username"
            class="min-w-0 flex-1 bg-transparent px-2.5 text-sm font-semibold text-slate-800 outline-none placeholder:font-medium placeholder:text-slate-400"
            placeholder="请输入用户名"
          />
        </span>
      </label>

      <label class="block">
        <span class="mb-1.5 block text-xs font-bold text-slate-500">邮箱</span>
        <span class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50/80 px-3 transition-colors focus-within:border-primary focus-within:bg-white focus-within:ring-2 focus-within:ring-primary/15">
          <Mail class="h-4 w-4 text-slate-400" />
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            class="min-w-0 flex-1 bg-transparent px-2.5 text-sm font-semibold text-slate-800 outline-none placeholder:font-medium placeholder:text-slate-400"
            placeholder="you@example.com"
          />
        </span>
      </label>

      <label class="block">
        <span class="mb-1.5 block text-xs font-bold text-slate-500">密码</span>
        <span class="flex h-12 items-center rounded-2xl border border-slate-200 bg-slate-50/80 px-3 transition-colors focus-within:border-primary focus-within:bg-white focus-within:ring-2 focus-within:ring-primary/15">
          <Lock class="h-4 w-4 text-slate-400" />
          <input
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            class="min-w-0 flex-1 bg-transparent px-2.5 text-sm font-semibold text-slate-800 outline-none placeholder:font-medium placeholder:text-slate-400"
            placeholder="至少 6 位密码"
          />
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            @click="showPassword = !showPassword"
          >
            <EyeOff v-if="showPassword" class="h-4 w-4" />
            <Eye v-else class="h-4 w-4" />
          </button>
        </span>
      </label>

      <p v-if="message" class="rounded-lg border border-rose-100 bg-rose-50 px-3 py-2 text-xs font-medium text-rose-600">
        {{ message }}
      </p>

      <button
        type="submit"
        class="mt-1 flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 text-sm font-black text-white shadow-xl shadow-slate-950/15 transition-all hover:-translate-y-0.5 hover:bg-primary hover:shadow-primary/20 disabled:cursor-not-allowed disabled:translate-y-0 disabled:opacity-70"
        :disabled="loading"
      >
        <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
        {{ loading ? '处理中...' : buttonText }}
      </button>
    </form>

    <div class="mt-6 text-center text-sm font-medium text-slate-500">
      <template v-if="isRegister">
        已有账号？
        <RouterLink to="/login" class="font-black text-primary hover:text-secondary">去登录</RouterLink>
      </template>
      <template v-else>
        还没有账号？
        <RouterLink to="/register" class="font-black text-primary hover:text-secondary">去注册</RouterLink>
      </template>
    </div>
  </div>
</template>
