import { computed, reactive, ref } from "vue";
import { Ban, CheckCircle2, Coins, ReceiptText, UsersRound } from "lucide-vue-next";
import {
  adjustAdminUserCredits,
  getAdminCreditOrders,
  getAdminCreditTransactions,
  getAdminAuditLogs,
  getAdminImageTasks,
  getAdminSettings,
  getAdminOverview,
  getAdminUsers,
  updateAdminSettings,
  updateAdminUser,
} from "@/api/admin.js";
import { formatMoney, roleLabel, totalPages } from "@/constants/admin.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

const overview = ref(null);
const overviewLoading = ref(false);
const usersState = reactive(createPageState({ role: "", status: "" }));
const ordersState = reactive(createPageState({ status: "" }));
const transactionsState = reactive(createPageState({ type: "" }));
const imageTasksState = reactive(createPageState({ status: "", scenario: "" }));
const auditLogsState = reactive(createPageState({ action: "" }));
const settingsState = reactive({
  imageCreditCosts: { "1K": 1, "2K": 2, "4K": 4 },
  rechargePackages: [],
  paymentConfig: {},
  loading: false,
  saving: false,
});
const adjustModalOpen = ref(false);
const adjustTarget = ref(null);
const adjustSaving = ref(false);

const overviewCards = computed(() => {
  const data = overview.value || {};
  return [
    { label: "用户总数", value: data.total_users || 0, icon: UsersRound },
    { label: "今日新增", value: data.today_new_users || 0, icon: CheckCircle2 },
    { label: "累计充值", value: formatMoney(data.paid_amount_cents || 0), icon: ReceiptText },
    { label: "今日充值", value: formatMoney(data.today_paid_amount_cents || 0), icon: Coins },
    { label: "总积分余额", value: `${data.total_credit_balance || 0} 点`, icon: Coins },
    { label: "失败任务", value: data.failed_image_tasks || 0, icon: Ban },
  ];
});

export function useAdminDashboard() {
  const confirm = useConfirm();
  const toast = useToast();

  async function loadOverview() {
    overviewLoading.value = true;
    try {
      const result = await getAdminOverview();
      if (result.code !== 0) {
        toast.error(result.message || "加载概览失败");
        return;
      }
      overview.value = result.data || {};
    } catch {
      toast.error("加载概览失败");
    } finally {
      overviewLoading.value = false;
    }
  }

  async function loadPage(state, apiFn, filters, errorMessage) {
    state.loading = true;
    try {
      const result = await apiFn({
        page: state.page,
        page_size: state.pageSize,
        keyword: state.keyword || undefined,
        ...filters,
      });
      if (result.code !== 0) {
        toast.error(result.message || errorMessage);
        return;
      }
      state.items = result.data?.items || [];
      state.total = result.data?.total || 0;
    } catch {
      toast.error(errorMessage);
    } finally {
      state.loading = false;
    }
  }

  async function loadUsers() {
    await loadPage(
      usersState,
      getAdminUsers,
      {
        role: usersState.role || undefined,
        status: usersState.status || undefined,
      },
      "加载用户失败",
    );
  }

  async function loadOrders() {
    await loadPage(
      ordersState,
      getAdminCreditOrders,
      {
        status: ordersState.status || undefined,
      },
      "加载订单失败",
    );
  }

  async function loadTransactions() {
    await loadPage(
      transactionsState,
      getAdminCreditTransactions,
      {
        type: transactionsState.type || undefined,
      },
      "加载流水失败",
    );
  }

  async function loadImageTasks() {
    await loadPage(
      imageTasksState,
      getAdminImageTasks,
      {
        status: imageTasksState.status || undefined,
        scenario: imageTasksState.scenario || undefined,
      },
      "加载生图任务失败",
    );
  }

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

  function applyUsersFilter() {
    usersState.page = 1;
    loadUsers();
  }

  function applyOrdersFilter() {
    ordersState.page = 1;
    loadOrders();
  }

  function applyTransactionsFilter() {
    transactionsState.page = 1;
    loadTransactions();
  }

  function applyImageTasksFilter() {
    imageTasksState.page = 1;
    loadImageTasks();
  }

  function applyAuditLogsFilter() {
    auditLogsState.page = 1;
    loadAuditLogs();
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

  async function changeUserRole(user) {
    const nextRole = user.role === "super_admin" ? "user" : "super_admin";
    const ok = await confirm.open({
      title: nextRole === "super_admin" ? "设为超级管理员" : "取消超级管理员",
      message: `确定将 ${user.email} 设置为${roleLabel(nextRole)}吗？`,
      confirmText: "确认",
    });
    if (!ok) return;
    await saveUserPatch(user.id, { role: nextRole });
  }

  async function changeUserStatus(user) {
    const nextStatus = user.status === "disabled" ? "active" : "disabled";
    const ok = await confirm.open({
      title: nextStatus === "disabled" ? "禁用用户" : "启用用户",
      message: `确定${nextStatus === "disabled" ? "禁用" : "启用"} ${user.email} 吗？`,
      confirmText: nextStatus === "disabled" ? "禁用" : "启用",
      tone: nextStatus === "disabled" ? "danger" : "default",
    });
    if (!ok) return;
    await saveUserPatch(user.id, { status: nextStatus });
  }

  async function saveUserPatch(userId, payload) {
    try {
      const result = await updateAdminUser(userId, payload);
      if (result.code !== 0) {
        toast.error(result.message || "更新用户失败");
        return;
      }
      toast.success("用户已更新");
      await loadUsers();
      await loadOverview();
    } catch {
      toast.error("更新用户失败");
    }
  }

  function openAdjustModal(user) {
    adjustTarget.value = user;
    adjustModalOpen.value = true;
  }

  function closeAdjustModal() {
    adjustModalOpen.value = false;
  }

  async function submitAdjustCredits(payload) {
    const amount = Number(payload?.amount);
    if (!Number.isInteger(amount) || amount === 0) {
      toast.error("请输入非 0 整数积分");
      return;
    }
    const note = String(payload?.note || "").trim();
    if (!note) {
      toast.error("请填写调整备注");
      return;
    }
    adjustSaving.value = true;
    try {
      const result = await adjustAdminUserCredits(adjustTarget.value.id, {
        amount,
        note,
      });
      if (result.code !== 0) {
        toast.error(result.message || "调整积分失败");
        return;
      }
      toast.success("积分已调整");
      adjustModalOpen.value = false;
      await loadUsers();
      await loadOverview();
      await loadTransactions();
    } catch {
      toast.error("调整积分失败");
    } finally {
      adjustSaving.value = false;
    }
  }

  function changePage(state, loader, direction) {
    const nextPage = state.page + direction;
    if (nextPage < 1 || nextPage > totalPages(state)) return;
    state.page = nextPage;
    loader();
  }

  return {
    overviewCards,
    overviewLoading,
    usersState,
    ordersState,
    transactionsState,
    imageTasksState,
    auditLogsState,
    settingsState,
    adjustModalOpen,
    adjustTarget,
    adjustSaving,
    loadOverview,
    loadUsers,
    loadOrders,
    loadTransactions,
    loadImageTasks,
    loadAuditLogs,
    loadSettings,
    applyUsersFilter,
    applyOrdersFilter,
    applyTransactionsFilter,
    applyImageTasksFilter,
    applyAuditLogsFilter,
    addRechargePackage,
    removeRechargePackage,
    saveSettings,
    changeUserRole,
    changeUserStatus,
    openAdjustModal,
    closeAdjustModal,
    submitAdjustCredits,
    changePage,
  };
}

function createPageState(extra = {}) {
  return {
    items: [],
    total: 0,
    page: 1,
    pageSize: 20,
    keyword: "",
    loading: false,
    ...extra,
  };
}
