<script setup>
import { ExternalLink, LoaderCircle, QrCode, RefreshCw } from 'lucide-vue-next'
import { formatMoney } from '@/composables/billing/useRechargeOrder.js'

defineProps({
  order: { type: Object, required: true },
  qrDataUrl: { type: String, default: '' },
  error: { type: String, default: '' },
})
defineEmits(['retry'])
</script>

<template>
  <div class="grid gap-6 bg-white p-5 sm:p-6 md:grid-cols-[280px_1fr]">
    <div class="flex flex-col items-center rounded-2xl border border-slate-200 bg-slate-50 p-5">
      <div
        class="mb-4 inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-[11px] font-black text-slate-600 shadow-sm"
      >
        <QrCode class="h-3.5 w-3.5 text-emerald-600" />微信扫码支付
      </div>
      <div
        class="flex h-60 w-60 items-center justify-center rounded-2xl border border-slate-200 bg-white p-3 shadow-inner"
      >
        <img
          v-if="order.img"
          :src="order.img"
          class="h-full w-full object-contain"
          alt="微信支付二维码"
        /><img
          v-else-if="qrDataUrl"
          :src="qrDataUrl"
          class="h-full w-full object-contain"
          alt="微信支付二维码"
        /><LoaderCircle v-else class="h-6 w-6 animate-spin text-slate-300" />
      </div>
      <p class="mt-3 text-xs font-semibold text-slate-500">支付成功后自动到账</p>
    </div>
    <div class="flex flex-col justify-between gap-5">
      <div class="space-y-3">
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <p class="text-xs text-slate-400">订单号</p>
          <p class="mt-1 break-all text-xs font-bold text-slate-700">{{ order.out_trade_no }}</p>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <p class="text-xs text-slate-400">充值积分</p>
            <p class="mt-1 text-lg font-black text-emerald-600">{{ order.credits_to_add }} 点</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <p class="text-xs text-slate-400">支付金额</p>
            <p class="mt-1 text-lg font-black text-slate-950">
              {{ formatMoney(order.amount_cents) }}
            </p>
          </div>
        </div>
        <p class="rounded-xl bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">
          支付成功后会自动到账；如果页面未更新，请稍等几秒。
        </p>
        <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-600">
          {{ error }}
        </p>
      </div>
      <div class="flex gap-2">
        <a
          v-if="order.pay_url || order.qrcode"
          :href="order.pay_url || order.qrcode"
          target="_blank"
          rel="noreferrer"
          class="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
          ><ExternalLink class="h-4 w-4" />打开支付页</a
        ><button
          type="button"
          class="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
          @click="$emit('retry')"
        >
          <RefreshCw class="h-4 w-4" />更换套餐
        </button>
      </div>
    </div>
  </div>
</template>
