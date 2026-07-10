import { reactive } from "vue";
import { getAdminAuditLogs } from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";

export function useAdminAuditLogs() {
  const auditLogsState = reactive(createAdminPageState({ action: "" }));
  const toast = useToast();
  const { loadPage, applyFilter, changePage } = useAdminPageLoader(toast);

  async function loadAuditLogs() {
    await loadPage(
      auditLogsState,
      getAdminAuditLogs,
      {
        action: auditLogsState.action || undefined,
      },
      "加载审计日志失败",
    );
  }

  function applyAuditLogsFilter() {
    applyFilter(auditLogsState, loadAuditLogs);
  }

  return {
    auditLogsState,
    loadAuditLogs,
    applyAuditLogsFilter,
    changePage,
  };
}
