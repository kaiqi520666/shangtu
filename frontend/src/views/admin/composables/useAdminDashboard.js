import { computed, reactive, ref } from "vue";
import { Ban, CheckCircle2, Coins, ReceiptText, UsersRound } from "lucide-vue-next";
import {
  adjustAdminUserCredits,
  getAdminCreditOrders,
  getAdminCreditTransactions,
  getAdminOverview,
  getAdminUsers,
  updateAdminUser,
} from "@/api/admin.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";
import { formatMoney, roleLabel, totalPages } from "../adminFormatters.js";

export function useAdminDashboard() {
  const confirm = useConfirm();
  const toast = useToast();

  const overview = ref(null);
  const overviewLoading = ref(false);
  const usersState = reactive(createPageState({ role: "", status: "" }));
  const ordersState = reactive(createPageState({ status: "" }));
  const transactionsState = reactive(createPageState({ type: "" }));
  const adjustModalOpen = ref(false);
  const adjustTarget = ref(null);
  const adjustSaving = ref(false);
  const adjustForm = reactive({
    amount: "",
    note: "",
  });

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

  async function loadUsers() {
    usersState.loading = true;
    try {
      const result = await getAdminUsers({
        page: usersState.page,
        page_size: usersState.pageSize,
        keyword: usersState.keyword || undefined,
        role: usersState.role || undefined,
        status: usersState.status || undefined,
      });
      if (result.code !== 0) {
        toast.error(result.message || "加载用户失败");
        return;
      }
      usersState.items = result.data?.items || [];
      usersState.total = result.data?.total || 0;
    } catch {
      toast.error("加载用户失败");
    } finally {
      usersState.loading = false;
    }
  }

  async function loadOrders() {
    ordersState.loading = true;
    try {
      const result = await getAdminCreditOrders({
        page: ordersState.page,
        page_size: ordersState.pageSize,
        keyword: ordersState.keyword || undefined,
        status: ordersState.status || undefined,
      });
      if (result.code !== 0) {
        toast.error(result.message || "加载订单失败");
        return;
      }
      ordersState.items = result.data?.items || [];
      ordersState.total = result.data?.total || 0;
    } catch {
      toast.error("加载订单失败");
    } finally {
      ordersState.loading = false;
    }
  }

  async function loadTransactions() {
    transactionsState.loading = true;
    try {
      const result = await getAdminCreditTransactions({
        page: transactionsState.page,
        page_size: transactionsState.pageSize,
        keyword: transactionsState.keyword || undefined,
        type: transactionsState.type || undefined,
      });
      if (result.code !== 0) {
        toast.error(result.message || "加载流水失败");
        return;
      }
      transactionsState.items = result.data?.items || [];
      transactionsState.total = result.data?.total || 0;
    } catch {
      toast.error("加载流水失败");
    } finally {
      transactionsState.loading = false;
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
    adjustForm.amount = "";
    adjustForm.note = "";
    adjustModalOpen.value = true;
  }

  function closeAdjustModal() {
    adjustModalOpen.value = false;
  }

  async function submitAdjustCredits() {
    const amount = Number(adjustForm.amount);
    if (!Number.isInteger(amount) || amount === 0) {
      toast.error("请输入非 0 整数积分");
      return;
    }
    if (!adjustForm.note.trim()) {
      toast.error("请填写调整备注");
      return;
    }
    adjustSaving.value = true;
    try {
      const result = await adjustAdminUserCredits(adjustTarget.value.id, {
        amount,
        note: adjustForm.note.trim(),
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
    adjustModalOpen,
    adjustTarget,
    adjustSaving,
    adjustForm,
    loadOverview,
    loadUsers,
    loadOrders,
    loadTransactions,
    applyUsersFilter,
    applyOrdersFilter,
    applyTransactionsFilter,
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
