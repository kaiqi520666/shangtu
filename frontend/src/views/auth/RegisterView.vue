<script setup>
import { useRouter } from "vue-router";
import { register } from "@/api/auth.js";
import AuthForm from "@/components/auth/AuthForm.vue";
import AuthPageShell from "@/components/auth/AuthPageShell.vue";
import { useToast } from "@/composables/useToast.js";
import { useAuthStore } from "@/stores/auth.js";

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();

async function handleRegister(payload) {
  try {
    const result = await register({
      username: payload.username,
      email: payload.email,
      password: payload.password,
    });

    if (result.code !== 0) {
      toast.error(result.message || "注册失败");
      return;
    }

    authStore.login({
      username: result.data?.username || payload.username,
      email: result.data?.email || payload.email,
      token: result.data?.token,
      userId: result.data?.user_id,
      credits: result.data?.credits,
    });
    toast.success("注册成功");
    router.push("/generator");
  } catch (error) {
    toast.error(error.response?.data?.message || "注册失败，请稍后重试");
  }
}
</script>

<template>
  <AuthPageShell>
    <AuthForm mode="register" @submit="handleRegister" />
  </AuthPageShell>
</template>
