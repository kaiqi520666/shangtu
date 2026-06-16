<script setup>
import RechargeModal from '@/components/billing/RechargeModal.vue'
import GlobalConfirm from '@/components/ui/GlobalConfirm.vue'
import GlobalToast from '@/components/ui/GlobalToast.vue'
import { useRechargeModal } from '@/composables/useRechargeModal.js'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const { rechargeModalOpen, closeRechargeModal } = useRechargeModal()
</script>

<template>
  <DefaultLayout>
    <RouterView />
    <RechargeModal :open="rechargeModalOpen" @close="closeRechargeModal" />
    <GlobalToast />
    <GlobalConfirm />
  </DefaultLayout>
</template>
