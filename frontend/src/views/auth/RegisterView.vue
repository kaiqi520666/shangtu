<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { register } from "@/api/auth.js";
import AuthForm from "@/components/auth/AuthForm.vue";
import AuthPageShell from "@/components/auth/AuthPageShell.vue";
import { useToast } from "@/composables/useToast.js";
import { useAuthStore } from "@/stores/auth.js";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const toast = useToast();
const loading = ref(false);

async function handleRegister(payload) {
  if (loading.value) return;
  loading.value = true;
  try {
    const result = await register({
      username: payload.username,
      email: payload.email,
      password: payload.password,
      invite_code: typeof route.query.invite === "string" ? route.query.invite : undefined,
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
      consumption_multiplier: result.data?.consumption_multiplier,
      distribution_level: result.data?.distribution_level,
      distribution_enabled: result.data?.distribution_enabled,
    });
    toast.success("注册成功");
    router.push("/generator");
  } catch (error) {
    toast.error(error.response?.data?.message || "注册失败，请稍后重试");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <AuthPageShell>
    <div>
      <p v-if="route.query.invite" class="mb-3 text-center text-xs font-bold text-primary">邀请注册</p>
      <AuthForm mode="register" :loading="loading" @submit="handleRegister" />
    </div>
  </AuthPageShell>
</template>
