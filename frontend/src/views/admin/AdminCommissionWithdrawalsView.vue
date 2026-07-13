<script setup>
import { onMounted } from "vue";
import AdminCommissionWithdrawalsPanel from "@/components/admin/commission/AdminCommissionWithdrawalsPanel.vue";
import WithdrawalActionModal from "@/components/admin/commission/WithdrawalActionModal.vue";
import { useAdminCommissionWithdrawals } from "@/composables/admin/useAdminCommissionWithdrawals.js";

const distribution = useAdminCommissionWithdrawals();
onMounted(distribution.load);
</script>

<template>
  <AdminCommissionWithdrawalsPanel :state="distribution.state" @update-keyword="distribution.state.keyword = $event" @update-status="distribution.state.status = $event" @apply-filter="distribution.applyFilter" @change-page="distribution.changePage(distribution.state, distribution.load, $event)" @approve="distribution.approve" @reject="distribution.openAction('reject', $event)" @pay="distribution.openAction('pay', $event)" />
  <WithdrawalActionModal :action="distribution.action.value" :target="distribution.target.value" :saving="distribution.saving.value" @close="distribution.closeAction" @submit="distribution.submitAction" />
</template>
