import { reactive } from "vue";
import { getAdminSettings, updateAdminSettings } from "@/api/admin.js";
import { useAdminAuditLogs } from "@/composables/admin/useAdminAuditLogs.js";
import { useToast } from "@/composables/useToast.js";

const settingsState = reactive({
  imageCreditCosts: { "1K": 1, "2K": 2, "4K": 4 },
  rechargePackages: [],
  paymentConfig: {},
  loading: false,
  saving: false,
});

export function useAdminSettings() {
  const toast = useToast();
  const { loadAuditLogs } = useAdminAuditLogs();

  async function loadSettings() {
    settingsState.loading = true;
    try {
      const result = await getAdminSettings();
      if (result.code !== 0) {
        toast.error(result.message || "加载系统配置失败");
        return;
      }
      settingsState.imageCreditCosts = { ...(result.data?.image_credit_costs || {}) };
      settingsState.rechargePackages = (result.data?.recharge_packages || []).map((item) => ({ ...item }));
      settingsState.paymentConfig = result.data?.payment_config || {};
    } catch {
      toast.error("加载系统配置失败");
    } finally {
      settingsState.loading = false;
    }
  }

  function addRechargePackage() {
    settingsState.rechargePackages.push({
      id: `p_${Date.now()}`,
      name: "新套餐",
      credits: 100,
      amount_cents: 990,
      badge: "",
      enabled: true,
    });
  }

  function removeRechargePackage(index) {
    settingsState.rechargePackages.splice(index, 1);
  }

  async function saveSettings() {
    settingsState.saving = true;
    try {
      const payload = {
        image_credit_costs: {
          "1K": Number(settingsState.imageCreditCosts["1K"]),
          "2K": Number(settingsState.imageCreditCosts["2K"]),
          "4K": Number(settingsState.imageCreditCosts["4K"]),
        },
        recharge_packages: settingsState.rechargePackages.map((item) => ({
          id: String(item.id || "").trim(),
          name: String(item.name || "").trim(),
          credits: Number(item.credits),
          amount_cents: Number(item.amount_cents),
          badge: String(item.badge || "").trim(),
          enabled: Boolean(item.enabled),
        })),
      };
      const result = await updateAdminSettings(payload);
      if (result.code !== 0) {
        toast.error(result.message || "保存系统配置失败");
        return;
      }
      toast.success("系统配置已保存");
      await loadSettings();
      await loadAuditLogs();
    } catch {
      toast.error("保存系统配置失败");
    } finally {
      settingsState.saving = false;
    }
  }

  return {
    settingsState,
    loadSettings,
    addRechargePackage,
    removeRechargePackage,
    saveSettings,
  };
}
