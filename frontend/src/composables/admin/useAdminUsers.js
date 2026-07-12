import { reactive, ref } from "vue";
import { adjustAdminUserCredits, getAdminUsers, updateAdminUser, updateAdminUserBusiness } from "@/api/admin.js";
import { roleLabel } from "@/constants/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useAdminOverview } from "@/composables/admin/useAdminOverview.js";
import { useAdminTransactions } from "@/composables/admin/useAdminTransactions.js";
import { useAdminPasswordReset } from "@/composables/admin/useAdminPasswordReset.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

export function useAdminUsers() {
  const usersState = reactive(createAdminPageState({ role: "", status: "" }));
  const adjustModalOpen = ref(false);
  const adjustTarget = ref(null);
  const adjustSaving = ref(false);
  const businessModalOpen = ref(false);
  const businessTarget = ref(null);
  const businessSaving = ref(false);
  const confirm = useConfirm();
  const toast = useToast();
  const { loadPage, applyFilter, changePage } = useAdminPageLoader(toast);
  const { loadOverview } = useAdminOverview();
  const { loadTransactions } = useAdminTransactions();

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

  const passwordReset = useAdminPasswordReset(loadUsers);

  function applyUsersFilter() {
    applyFilter(usersState, loadUsers);
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

  function openBusinessModal(user) {
    businessTarget.value = user;
    businessModalOpen.value = true;
  }

  function closeBusinessModal() {
    businessModalOpen.value = false;
  }

  async function submitBusinessSettings(payload) {
    const multiplier = Number(payload.consumption_multiplier);
    const rate = Number(payload.commission_rate);
    if (multiplier < 0.01 || multiplier > 9.99 || (payload.commission_rate !== undefined && (rate < 0 || rate > 100))) {
      toast.error("请输入有效的倍率和佣金比例");
      return;
    }
    businessSaving.value = true;
    try {
      const result = await updateAdminUserBusiness(businessTarget.value.id, payload);
      if (result.code !== 0) return toast.error(result.message || "更新业务设置失败");
      toast.success("业务设置已更新");
      businessModalOpen.value = false;
      await loadUsers();
    } catch {
      toast.error("更新业务设置失败");
    } finally {
      businessSaving.value = false;
    }
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

  return {
    usersState,
    adjustModalOpen,
    adjustTarget,
    adjustSaving,
    businessModalOpen,
    businessTarget,
    businessSaving,
    passwordReset,
    loadUsers,
    applyUsersFilter,
    changeUserRole,
    changeUserStatus,
    openAdjustModal,
    closeAdjustModal,
    openBusinessModal,
    closeBusinessModal,
    submitBusinessSettings,
    submitAdjustCredits,
    changePage,
  };
}
