<script setup>
import { onMounted } from "vue";
import AdminAuditLogsPanel from "@/components/admin/AdminAuditLogsPanel.vue";
import { useAdminDashboard } from "@/composables/useAdminDashboard.js";

const { auditLogsState, loadAuditLogs, applyAuditLogsFilter, changePage } = useAdminDashboard();

onMounted(() => {
  loadAuditLogs();
});
</script>

<template>
  <AdminAuditLogsPanel
    :state="auditLogsState"
    @apply-filter="applyAuditLogsFilter"
    @change-page="changePage(auditLogsState, loadAuditLogs, $event)"
  />
</template>
