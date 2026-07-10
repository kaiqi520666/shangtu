import { describe, expect, it } from "vitest";
import { useAdminAuditLogs } from "./useAdminAuditLogs.js";
import { useAdminOverview } from "./useAdminOverview.js";
import { useAdminUsers } from "./useAdminUsers.js";

describe("admin composable state isolation", () => {
  it("creates independent list and modal state per instance", () => {
    const auditA = useAdminAuditLogs();
    const auditB = useAdminAuditLogs();
    const usersA = useAdminUsers();
    const usersB = useAdminUsers();

    auditA.auditLogsState.keyword = "first";
    usersA.adjustModalOpen.value = true;

    expect(auditB.auditLogsState.keyword).toBe("");
    expect(usersB.adjustModalOpen.value).toBe(false);
  });

  it("creates independent overview loading state", () => {
    const first = useAdminOverview();
    const second = useAdminOverview();

    first.overviewLoading.value = true;

    expect(second.overviewLoading.value).toBe(false);
  });
});
