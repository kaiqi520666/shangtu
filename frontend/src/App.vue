<script setup>
import { defineAsyncComponent } from 'vue'
import GlobalConfirm from '@/components/ui/GlobalConfirm.vue'
import GlobalToast from '@/components/ui/GlobalToast.vue'
import { useRechargeModal } from '@/composables/useRechargeModal.js'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const { rechargeModalOpen, closeRechargeModal } = useRechargeModal()
const RechargeModal = defineAsyncComponent(() => import('@/components/billing/RechargeModal.vue'))
</script>

<template>
  <DefaultLayout>
    <RouterView />
    <RechargeModal v-if="rechargeModalOpen" :open="true" @close="closeRechargeModal" />
    <GlobalToast />
    <GlobalConfirm />
  </DefaultLayout>
</template>
