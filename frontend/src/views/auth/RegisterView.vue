<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getCaptchaConfig, register, sendRegistrationEmailCode } from "@/api/auth.js";
import AuthForm from "@/components/auth/AuthForm.vue";
import AuthPageShell from "@/components/auth/AuthPageShell.vue";
import { useToast } from "@/composables/useToast.js";
import { useAuthStore } from "@/stores/auth.js";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const toast = useToast();
const loading = ref(false);
const codeLoading = ref(false);
const codeCooldown = ref(0);
const captchaSiteKey = ref("");
const authForm = ref(null);
let cooldownTimer;

onMounted(async () => {
  try {
    const result = await getCaptchaConfig();
    if (result.code === 0) captchaSiteKey.value = result.data?.site_key || "";
  } catch {
    toast.error("人机验证配置加载失败");
  }
});

async function handleSendCode({ email, captchaToken }) {
  if (codeLoading.value || codeCooldown.value > 0) return;
  codeLoading.value = true;
  try {
    const result = await sendRegistrationEmailCode({
      email,
      captcha_token: captchaToken,
    });
    if (result.code !== 0) {
      toast.error(result.message || "验证码发送失败");
      return;
    }
    codeCooldown.value = result.data?.cooldown_seconds || 60;
    cooldownTimer = window.setInterval(() => {
      codeCooldown.value -= 1;
      if (codeCooldown.value <= 0) window.clearInterval(cooldownTimer);
    }, 1000);
    toast.success("验证码已发送");
  } catch (error) {
    toast.error(error.response?.data?.message || "验证码发送失败，请稍后重试");
  } finally {
    codeLoading.value = false;
    authForm.value?.resetCaptcha();
  }
}

onBeforeUnmount(() => window.clearInterval(cooldownTimer));

async function handleRegister(payload) {
  if (loading.value) return;
  loading.value = true;
  try {
    const result = await register({
      username: payload.username,
      email: payload.email,
      password: payload.password,
      verification_code: payload.verificationCode,
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
      <AuthForm
        ref="authForm"
        mode="register"
        :loading="loading"
        :code-loading="codeLoading"
        :code-cooldown="codeCooldown"
        :captcha-required="codeCooldown === 0"
        :captcha-site-key="captchaSiteKey"
        captcha-action="register_email"
        @send-code="handleSendCode"
        @submit="handleRegister"
      />
    </div>
  </AuthPageShell>
</template>
