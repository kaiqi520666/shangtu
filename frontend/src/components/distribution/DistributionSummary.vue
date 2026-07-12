<script setup>
import { Copy, WalletCards } from "lucide-vue-next";
import { computed } from "vue";
import { formatMoney } from "@/constants/admin.js";
import { useToast } from "@/composables/useToast.js";

const props = defineProps({ overview: { type: Object, required: true } });
const emit = defineEmits(["withdraw"]);
const toast = useToast();
const inviteUrl = computed(() => props.overview.invite_code ? `${window.location.origin}/register?invite=${props.overview.invite_code}` : "");

async function copyInvite() {
  await navigator.clipboard.writeText(inviteUrl.value);
  toast.success("邀请链接已复制");
}
</script>

<template>
  <div class="grid gap-4 md:grid-cols-3">
    <div class="rounded-lg border border-slate-200 bg-white p-5"><p class="text-xs font-bold text-slate-500">可提现佣金</p><p class="mt-2 text-3xl font-black text-slate-950">{{ formatMoney(overview.commission_available_cents) }}</p><button type="button" class="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('withdraw')"><WalletCards class="h-4 w-4" />申请提现</button></div>
    <div class="rounded-lg border border-slate-200 bg-white p-5"><p class="text-xs font-bold text-slate-500">冻结 / 已提现</p><p class="mt-2 text-xl font-black text-slate-900">{{ formatMoney(overview.commission_frozen_cents) }}</p><p class="mt-2 text-xs text-slate-400">累计已提现 {{ formatMoney(overview.commission_withdrawn_cents) }}</p></div>
    <div class="rounded-lg border border-slate-200 bg-white p-5"><p class="text-xs font-bold text-slate-500">分销等级与比例</p><p class="mt-2 text-xl font-black text-slate-900">{{ overview.level }} 级 · {{ Number(overview.commission_rate).toFixed(2) }}%</p><button v-if="inviteUrl" type="button" class="mt-4 inline-flex max-w-full items-center gap-2 text-xs font-bold text-primary" @click="copyInvite"><Copy class="h-4 w-4 shrink-0" /><span class="truncate">复制邀请链接</span></button></div>
  </div>
</template>
