<script setup>
import { onMounted } from "vue";
import AdminOrdersPanel from "@/components/admin/AdminOrdersPanel.vue";
import { useAdminOrders } from "@/composables/admin/useAdminOrders.js";

const { ordersState, loadOrders, applyOrdersFilter, changePage } = useAdminOrders();

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
