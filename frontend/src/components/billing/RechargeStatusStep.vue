<script setup>
import { CheckCircle2, RefreshCw } from 'lucide-vue-next'

defineProps({
  order: { type: Object, required: true },
  credits: { type: Number, default: 0 },
  timedOut: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['close', 'retry'])
</script>

<template>
  <div class="flex flex-col items-center gap-4 bg-white p-8 text-center">
    <div
      class="flex h-16 w-16 items-center justify-center rounded-2xl"
      :class="
        order.status === 'paid' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'
      "
    >
      <CheckCircle2 v-if="order.status === 'paid'" class="h-9 w-9" /><RefreshCw
        v-else
        class="h-8 w-8"
      />
    </div>
    <div v-if="order.status === 'paid'">
      <h3 class="text-lg font-black text-slate-950">充值成功</h3>
      <p class="mt-1 text-sm text-slate-500">
        已到账 {{ order.credits_to_add }} 点，当前余额 {{ credits }} 点
      </p>
    </div>
    <div v-else>
      <h3 class="text-lg font-black text-slate-950">
        {{ timedOut ? '等待支付超时' : '支付订单失败' }}
      </h3>
      <p class="mt-1 text-sm text-slate-500">
        {{ error || order.error_message || '请更换套餐或重新创建支付订单。' }}
      </p>
    </div>
    <button
      type="button"
      class="rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-bold text-white hover:bg-slate-800"
      @click="emit(order.status === 'paid' ? 'close' : 'retry')"
    >
      {{ order.status === 'paid' ? '完成' : '重新选择套餐' }}
    </button>
  </div>
</template>
