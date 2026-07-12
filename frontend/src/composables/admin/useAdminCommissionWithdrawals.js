import { reactive, ref } from "vue";
import { approveAdminCommissionWithdrawal, getAdminCommissionWithdrawals, payAdminCommissionWithdrawal, rejectAdminCommissionWithdrawal } from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

export function useAdminCommissionWithdrawals() {
  const state = reactive(createAdminPageState({ status: "", keyword: "" }));
  const action = ref(null);
  const target = ref(null);
  const saving = ref(false);
  const toast = useToast();
  const confirm = useConfirm();
  const { loadPage, applyFilter, changePage } = useAdminPageLoader(toast);

  async function load() {
    await loadPage(state, getAdminCommissionWithdrawals, { status: state.status || undefined, keyword: state.keyword || undefined }, "加载提现申请失败");
  }

  async function approve(item) {
    const ok = await confirm.open({ title: "通过提现审核", message: `确认通过 ${item.user_email} 的提现申请吗？`, confirmText: "通过" });
    if (!ok) return;
    const result = await approveAdminCommissionWithdrawal(item.id);
    if (result.code !== 0) return toast.error(result.message || "审核失败");
    toast.success("审核已通过");
    load();
  }

  function openAction(type, item) {
    action.value = type;
    target.value = item;
  }

  function closeAction() {
    action.value = null;
    target.value = null;
  }

  async function submitAction(payload) {
    saving.value = true;
    try {
      const result = action.value === "reject"
        ? await rejectAdminCommissionWithdrawal(target.value.id, payload.reason)
        : await payAdminCommissionWithdrawal(target.value.id, payload);
      if (result.code !== 0) return toast.error(result.message || "操作失败");
      toast.success(action.value === "reject" ? "申请已驳回" : "打款已确认");
      closeAction();
      await load();
    } catch {
      toast.error("操作失败");
    } finally {
      saving.value = false;
    }
  }

  return { state, action, target, saving, load, approve, openAction, closeAction, submitAction, applyFilter: () => applyFilter(state, load), changePage };
}
