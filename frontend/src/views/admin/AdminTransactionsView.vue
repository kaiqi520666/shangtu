<script setup>
import { onMounted } from "vue";
import AdminTransactionsPanel from "@/components/admin/AdminTransactionsPanel.vue";
import { useAdminDashboard } from "@/composables/useAdminDashboard.js";

const { transactionsState, loadTransactions, applyTransactionsFilter, changePage } = useAdminDashboard();

onMounted(() => {
  loadTransactions();
});
</script>

<template>
  <AdminTransactionsPanel
    :state="transactionsState"
    @apply-filter="applyTransactionsFilter"
    @change-page="changePage(transactionsState, loadTransactions, $event)"
  />
</template>
