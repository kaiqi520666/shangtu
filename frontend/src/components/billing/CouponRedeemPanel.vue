<script setup>
import { ref } from "vue";
import { CircleCheck, LoaderCircle, TicketPercent } from "lucide-vue-next";
import { redeemCouponCode } from "@/api/billing.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";

const code = ref("");
const redeeming = ref(false);
const redemption = ref(null);
const toast = useToast();

async function redeem() {
  const normalized = code.value.trim().toUpperCase();
  if (!/^[A-Z0-9-]{4,32}$/.test(normalized)) {
    toast.error("请输入 4～32 位字母、数字或连字符组成的优惠码");
    return;
  }
  redeeming.value = true;
  try {
    const result = await redeemCouponCode(normalized);
    if (result.code !== 0) return toast.error(result.message || "优惠码兑换失败");
    redemption.value = result.data;
    code.value = "";
    toast.success(`已获得 ${result.data.credits_added} 积分`);
  } catch (error) {
    toast.error(getApiErrorMessage(error, "优惠码兑换失败"));
  } finally {
    redeeming.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-[420px] items-center justify-center rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
    <div class="w-full max-w-lg">
      <div v-if="redemption" class="mb-4 flex items-center gap-3 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3">
        <CircleCheck class="h-6 w-6 shrink-0 text-emerald-600" />
        <div>
          <p class="text-sm font-black text-emerald-800">已到账 {{ redemption.credits_added.toLocaleString() }} 积分</p>
          <p class="mt-0.5 text-xs font-semibold text-emerald-600">当前余额 {{ redemption.credits.toLocaleString() }} 点</p>
        </div>
      </div>
      <form class="space-y-3" @submit.prevent="redeem">
        <label class="block">
          <span class="mb-1.5 block text-xs font-bold text-slate-600">优惠码</span>
          <span class="flex h-12 items-center rounded-xl border border-slate-200 px-3 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/15">
            <TicketPercent class="h-5 w-5 shrink-0 text-slate-400" />
            <input v-model.trim="code" type="text" maxlength="32" autocomplete="off" class="min-w-0 flex-1 bg-transparent px-3 text-sm font-bold uppercase text-slate-800 outline-none placeholder:font-medium placeholder:text-slate-400" placeholder="请输入优惠码" />
          </span>
        </label>
        <button type="submit" class="flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 text-sm font-black text-white hover:bg-slate-800 disabled:opacity-60" :disabled="redeeming">
          <LoaderCircle v-if="redeeming" class="h-4 w-4 animate-spin" />
          <TicketPercent v-else class="h-4 w-4 text-emerald-300" />
          {{ redeeming ? "兑换中..." : "立即兑换" }}
        </button>
      </form>
    </div>
  </div>
</template>
