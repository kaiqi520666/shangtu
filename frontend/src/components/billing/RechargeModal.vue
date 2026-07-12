<script setup>
import { toRef } from 'vue'
import { BadgeDollarSign, WalletCards } from 'lucide-vue-next'
import RechargePackageStep from '@/components/billing/RechargePackageStep.vue'
import RechargePaymentStep from '@/components/billing/RechargePaymentStep.vue'
import RechargeStatusStep from '@/components/billing/RechargeStatusStep.vue'
import AppModal from '@/components/ui/AppModal.vue'
import { formatCredits, useRechargeOrder } from '@/composables/billing/useRechargeOrder.js'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])
const order = useRechargeOrder(toRef(props, 'open'))

function closeModal() {
  order.clearPolling()
  emit('close')
}
</script>

<template>
  <AppModal
    :open="open"
    panel-class="w-full max-w-3xl border-slate-200/80 shadow-[0_28px_90px_rgba(15,23,42,0.32)]"
    @close="closeModal"
  >
    <template #header>
      <div class="flex min-w-0 flex-1 items-center justify-between gap-4 pr-4">
        <div class="flex min-w-0 items-center gap-3">
          <div
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-emerald-300 shadow-sm"
          >
            <WalletCards class="h-5 w-5" />
          </div>
          <div class="min-w-0">
            <h3 class="text-base font-black text-slate-950">{{ order.modalTitle.value }}</h3>
            <p class="mt-0.5 text-xs font-medium text-slate-500">
              当前 {{ formatCredits(order.authStore.credits) }} 点
            </p>
          </div>
        </div>
        <RouterLink
          to="/account/pricing"
          class="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
          @click="closeModal"
          ><BadgeDollarSign class="h-4 w-4 text-emerald-600" />计费标准</RouterLink
        >
      </div>
    </template>

    <RechargePackageStep
      v-if="!order.currentOrder.value"
      :mode="order.mode.value"
      :loading="order.loadingPackages.value"
      :packages="order.packages.value"
      :selected-id="order.selectedPackageId.value"
      :selected-package="order.selectedPackage.value"
      :creating="order.creatingOrder.value"
      @update:mode="order.mode.value = $event"
      @select="order.selectedPackageId.value = $event"
      @create="order.createOrder"
    />
    <RechargeStatusStep
      v-else-if="
        order.currentOrder.value.status === 'paid' ||
        order.currentOrder.value.status === 'failed' ||
        order.paymentTimedOut.value
      "
      :order="order.currentOrder.value"
      :credits="order.authStore.credits"
      :timed-out="order.paymentTimedOut.value"
      :error="order.pollError.value"
      @close="closeModal"
      @retry="order.resetToPackages"
    />
    <RechargePaymentStep
      v-else
      :order="order.currentOrder.value"
      :qr-data-url="order.qrDataUrl.value"
      :error="order.pollError.value"
      @retry="order.resetToPackages"
    />
  </AppModal>
</template>
