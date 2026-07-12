import { reactive, ref } from "vue";
import {
  createAdminCouponCode,
  deleteAdminCouponCode,
  getAdminCouponCodes,
  updateAdminCouponCode,
} from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";

export function useAdminCouponCodes() {
  const state = reactive(createAdminPageState({ status: "" }));
  const modalOpen = ref(false);
  const target = ref(null);
  const saving = ref(false);
  const toast = useToast();
  const confirm = useConfirm();
  const { loadPage, applyFilter: applyPageFilter, changePage: changeAdminPage } = useAdminPageLoader(toast);

  async function loadCouponCodes() {
    await loadPage(
      state,
      getAdminCouponCodes,
      { status: state.status || undefined },
      "加载优惠码失败",
    );
  }

  function applyFilter() {
    applyPageFilter(state, loadCouponCodes);
  }

  function changePage(direction) {
    changeAdminPage(state, loadCouponCodes, direction);
  }

  function openCreate() {
    target.value = null;
    modalOpen.value = true;
  }

  function openEdit(item) {
    target.value = item;
    modalOpen.value = true;
  }

  async function saveCoupon(form) {
    const payload = normalizeForm(form);
    if (!payload) return;
    saving.value = true;
    try {
      const result = target.value
        ? await updateAdminCouponCode(target.value.id, payload)
        : await createAdminCouponCode(payload);
      if (result.code !== 0) return toast.error(result.message || "保存优惠码失败");
      toast.success(target.value ? "优惠码已更新" : "优惠码已创建");
      modalOpen.value = false;
      await loadCouponCodes();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "保存优惠码失败"));
    } finally {
      saving.value = false;
    }
  }

  async function toggleCoupon(item) {
    try {
      const result = await updateAdminCouponCode(item.id, { enabled: !item.enabled });
      if (result.code !== 0) return toast.error(result.message || "更新优惠码失败");
      toast.success(item.enabled ? "优惠码已停用" : "优惠码已启用");
      await loadCouponCodes();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "更新优惠码失败"));
    }
  }

  async function removeCoupon(item) {
    const approved = await confirm.open({
      title: "删除优惠码",
      message: `确定删除 ${item.code} 吗？删除后不可再次使用，历史兑换记录会保留。`,
      confirmText: "删除",
      tone: "danger",
    });
    if (!approved) return;
    try {
      const result = await deleteAdminCouponCode(item.id);
      if (result.code !== 0) return toast.error(result.message || "删除优惠码失败");
      toast.success("优惠码已删除");
      await loadCouponCodes();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "删除优惠码失败"));
    }
  }

  function normalizeForm(form) {
    const code = String(form.code || "").trim().toUpperCase();
    if (!target.value && !/^[A-Z0-9-]{4,32}$/.test(code)) {
      toast.error("优惠码只能包含 4～32 位字母、数字或连字符");
      return null;
    }
    const credits = Number(form.credits);
    const usageLimit = form.unlimited ? null : Number(form.usageLimit);
    if (!Number.isInteger(credits) || credits < 1 || credits > 10000000) {
      toast.error("赠送积分必须是 1～10,000,000 的整数");
      return null;
    }
    if (usageLimit !== null && (!Number.isInteger(usageLimit) || usageLimit < 1 || usageLimit > 1000000)) {
      toast.error("使用上限必须是 1～1,000,000 的整数");
      return null;
    }
    const payload = { credits, usage_limit: usageLimit, enabled: Boolean(form.enabled) };
    if (!target.value) payload.code = code;
    return payload;
  }

  return {
    state,
    modalOpen,
    target,
    saving,
    loadCouponCodes,
    applyFilter,
    changePage,
    openCreate,
    openEdit,
    saveCoupon,
    toggleCoupon,
    removeCoupon,
  };
}
