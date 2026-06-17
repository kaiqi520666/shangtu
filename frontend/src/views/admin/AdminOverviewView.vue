<script setup>
import { onMounted } from "vue";
import AdminOverviewPanel from "@/components/admin/AdminOverviewPanel.vue";
import { useAdminOverview } from "@/composables/admin/useAdminOverview.js";

const { overviewCards, overviewLoading, loadOverview } = useAdminOverview();

onMounted(() => {
  loadOverview();
});
</script>

<template>
  <AdminOverviewPanel :cards="overviewCards" :loading="overviewLoading" />
</template>
