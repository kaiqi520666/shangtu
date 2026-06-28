<script setup>
import { onMounted } from "vue";
import AdminAuditLogsPanel from "@/components/admin/audit/AdminAuditLogsPanel.vue";
import { useAdminAuditLogs } from "@/composables/admin/useAdminAuditLogs.js";

const { auditLogsState, loadAuditLogs, applyAuditLogsFilter, changePage } = useAdminAuditLogs();

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
