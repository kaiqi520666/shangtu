<script setup>
import { computed, onMounted } from "vue";
import { CalendarDays, CreditCard, Mail, ShieldCheck, UserRound, WalletCards } from "lucide-vue-next";
import { useRechargeModal } from "@/composables/useRechargeModal.js";
import { useAccountProfile } from "@/composables/account/useAccountProfile.js";
import { formatTime, roleLabel, statusLabel } from "@/constants/admin.js";
import { useAuthStore } from "@/stores/auth.js";

const authStore = useAuthStore();
const { openRechargeModal } = useRechargeModal();
const { profile, loading, loadProfile } = useAccountProfile();

const account = computed(() => profile.value || authStore.user || {});
const initials = computed(() => {
  const source = account.value.email?.split("@")[0] || account.value.username || "VIP";
  return source.slice(0, 2).toUpperCase();
});

onMounted(() => {
  loadProfile();
});
</script>

<template>
  <section class="mx-auto max-w-5xl space-y-5">
    <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex flex-col gap-5 border-b border-slate-100 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex min-w-0 items-center gap-4">
          <span class="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-xl font-black text-emerald-600">
            {{ initials }}
          </span>
          <div class="min-w-0">
            <p class="truncate text-lg font-black text-slate-950">{{ account.email || "-" }}</p>
            <p class="mt-1 text-sm font-semibold text-slate-500">商图 AI · {{ account.plan || "SaaS Pro" }}</p>
          </div>
        </div>
        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-black text-white hover:bg-slate-800"
          @click="openRechargeModal"
        >
          <WalletCards class="h-4 w-4 text-emerald-300" />
          充值积分
        </button>
      </div>

      <div v-if="loading" class="px-5 py-10 text-center text-sm text-slate-400">正在加载账号信息...</div>
      <div v-else class="grid gap-4 p-5 md:grid-cols-4">
        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
            <CreditCard class="h-4 w-4 text-emerald-600" />
            当前积分
          </div>
          <p class="mt-3 text-3xl font-black text-slate-950">{{ account.credits || 0 }} <span class="text-sm text-slate-400">点</span></p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
            <UserRound class="h-4 w-4 text-slate-400" />
            用户名
          </div>
          <p class="mt-3 truncate text-sm font-black text-slate-900">{{ account.username || "-" }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
            <ShieldCheck class="h-4 w-4 text-slate-400" />
            账号状态
          </div>
          <p class="mt-3 text-sm font-black text-slate-900">{{ roleLabel(account.role) }} · {{ statusLabel(account.status) }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
            <CalendarDays class="h-4 w-4 text-slate-400" />
            注册时间
          </div>
          <p class="mt-3 text-sm font-black text-slate-900">{{ formatTime(account.created_at) }}</p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="flex items-center gap-2 text-sm font-black text-slate-900">
          <Mail class="h-4 w-4 text-slate-400" />
          登录账号
        </div>
        <p class="mt-3 break-all text-sm font-semibold text-slate-600">{{ account.email || "-" }}</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="flex items-center gap-2 text-sm font-black text-slate-900">
          <WalletCards class="h-4 w-4 text-emerald-600" />
          积分说明
        </div>
        <p class="mt-3 text-sm leading-6 text-slate-500">积分用于图片和视频生成，扣费按当前系统配置执行。充值、生成消耗、失败退回都会记录在积分明细中。</p>
      </div>
    </div>
  </section>
</template>
