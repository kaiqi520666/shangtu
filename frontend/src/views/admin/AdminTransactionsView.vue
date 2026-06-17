<script setup>
import { onMounted } from "vue";
import AdminTransactionsPanel from "@/components/admin/AdminTransactionsPanel.vue";
import { useAdminTransactions } from "@/composables/admin/useAdminTransactions.js";

const { transactionsState, loadTransactions, applyTransactionsFilter, changePage } = useAdminTransactions();

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
