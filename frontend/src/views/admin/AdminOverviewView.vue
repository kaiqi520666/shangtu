<script setup>
import { onMounted } from "vue";
import AdminOverviewPanel from "@/components/admin/AdminOverviewPanel.vue";
import { useAdminDashboard } from "@/composables/useAdminDashboard.js";

const { overviewCards, overviewLoading, loadOverview } = useAdminDashboard();

onMounted(() => {
  loadOverview();
});
</script>

<template>
  <AdminOverviewPanel :cards="overviewCards" :loading="overviewLoading" />
</template>
