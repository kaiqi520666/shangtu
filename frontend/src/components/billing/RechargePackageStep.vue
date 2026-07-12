<script setup>
import { CheckCircle2, CreditCard, LoaderCircle, TicketPercent } from 'lucide-vue-next'
import CouponRedeemPanel from '@/components/billing/CouponRedeemPanel.vue'
import { formatCredits, formatMoney } from '@/composables/billing/useRechargeOrder.js'

defineProps({
  mode: { type: String, required: true },
  loading: { type: Boolean, default: false },
  packages: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  selectedPackage: { type: Object, default: null },
  creating: { type: Boolean, default: false },
})
const emit = defineEmits(['update:mode', 'select', 'create'])
</script>

<template>
  <div class="min-h-0 space-y-3 overflow-y-auto bg-gradient-to-b from-slate-50/70 to-white p-4">
    <div
      class="mx-auto grid w-full max-w-sm grid-cols-2 rounded-lg border border-slate-200 bg-slate-100 p-1 shadow-inner"
    >
      <button
        v-for="item in [
          { value: 'packages', label: '充值积分', icon: CreditCard },
          { value: 'coupon', label: '优惠码兑换', icon: TicketPercent },
        ]"
        :key="item.value"
        type="button"
        class="flex h-10 items-center justify-center gap-2 rounded-md px-4 text-xs font-black transition-all"
        :class="
          mode === item.value
            ? 'bg-white text-slate-950 shadow-sm ring-1 ring-slate-200'
            : 'text-slate-500 hover:text-slate-700'
        "
        @click="emit('update:mode', item.value)"
      >
        <component
          :is="item.icon"
          class="h-4 w-4"
          :class="mode === item.value ? 'text-emerald-600' : 'text-slate-400'"
        />{{ item.label }}
      </button>
    </div>
    <div v-if="mode === 'packages'" class="min-h-[420px] space-y-3">
      <div v-if="loading" class="flex h-48 items-center justify-center text-sm text-slate-400">
        <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />正在加载套餐...
      </div>
      <div v-else-if="packages.length" class="grid gap-2 sm:grid-cols-3">
        <button
          v-for="pkg in packages"
          :key="pkg.id"
          type="button"
          class="group relative flex min-h-[112px] flex-col items-center justify-center rounded-2xl border px-4 py-4 text-center transition-all duration-200"
          :class="
            selectedId === pkg.id
              ? 'border-emerald-400 bg-emerald-50/80 text-slate-950 shadow-sm ring-1 ring-emerald-200'
              : 'border-slate-200 bg-white text-slate-950 shadow-sm hover:border-emerald-200'
          "
          @click="emit('select', pkg.id)"
        >
          <CheckCircle2
            v-if="selectedId === pkg.id"
            class="absolute right-3 top-3 h-4 w-4 text-emerald-500"
          />
          <p class="text-xl font-black text-slate-950">{{ formatCredits(pkg.credits) }} 积分</p>
          <p class="mt-2 text-sm font-bold text-slate-500">{{ formatMoney(pkg.amount_cents) }}</p>
        </button>
      </div>
      <div
        v-else
        class="flex h-40 items-center justify-center rounded-2xl border border-dashed border-slate-200 text-sm font-semibold text-slate-400"
      >
        暂无可用充值套餐
      </div>
      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-black text-white disabled:opacity-60"
        :disabled="!selectedPackage || creating"
        @click="emit('create')"
      >
        <LoaderCircle v-if="creating" class="h-4 w-4 animate-spin" /><CreditCard
          v-else
          class="h-4 w-4 text-emerald-300"
        />{{
          creating
            ? '正在创建订单...'
            : selectedPackage
              ? `微信支付 ${formatMoney(selectedPackage.amount_cents)}`
              : '选择套餐'
        }}
      </button>
    </div>
    <CouponRedeemPanel v-else />
  </div>
</template>
