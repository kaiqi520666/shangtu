<script setup>
import { onMounted } from "vue";
import AdminOrdersPanel from "@/components/admin/AdminOrdersPanel.vue";
import { useAdminDashboard } from "@/composables/useAdminDashboard.js";

const { ordersState, loadOrders, applyOrdersFilter, changePage } = useAdminDashboard();

onMounted(() => {
  loadOrders();
});
</script>

<template>
  <AdminOrdersPanel
    :state="ordersState"
    @apply-filter="applyOrdersFilter"
    @change-page="changePage(ordersState, loadOrders, $event)"
  />
</template>
