import { reactive, ref } from "vue";
import { createCommissionWithdrawal, getCommissionTransactions, getCommissionWithdrawals, getDistributionDownlines, getDistributionOverview, updateDistributionDownlineRate } from "@/api/account.js";
import { createAccountPageState } from "@/composables/account/useAccountTransactions.js";
import { useToast } from "@/composables/useToast.js";

export function useDistributionCenter() {
  const overview = reactive({ loading: true, level: null, commission_rate: 0, invite_code: "", commission_available_cents: 0, commission_frozen_cents: 0, commission_withdrawn_cents: 0 });
  const downlines = reactive(createAccountPageState());
  const transactions = reactive(createAccountPageState());
  const withdrawals = reactive(createAccountPageState());
  const withdrawalOpen = ref(false);
  const saving = ref(false);
  const toast = useToast();

  async function loadOverview() {
    const result = await getDistributionOverview();
    if (result.code !== 0) return toast.error(result.message || "加载分销账户失败");
    Object.assign(overview, result.data, { loading: false });
  }

  async function loadPage(state, request) {
    state.loading = true;
    try {
      const result = await request({ page: state.page, page_size: state.pageSize });
      if (result.code !== 0) return toast.error(result.message || "加载数据失败");
      Object.assign(state, result.data);
    } finally {
      state.loading = false;
    }
  }

  async function loadAll() {
    await Promise.all([loadOverview(), loadPage(downlines, getDistributionDownlines), loadPage(transactions, getCommissionTransactions), loadPage(withdrawals, getCommissionWithdrawals)]);
  }

  function changePage(state, request, delta) {
    const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
    const nextPage = state.page + delta;
    if (nextPage < 1 || nextPage > totalPages) return;
    state.page = nextPage;
    loadPage(state, request);
  }

  async function updateRate(userId, rate) {
    const result = await updateDistributionDownlineRate(userId, Number(rate));
    if (result.code !== 0) return toast.error(result.message || "更新比例失败");
    toast.success("下级比例已更新");
    await loadPage(downlines, getDistributionDownlines);
  }

  async function submitWithdrawal(payload) {
    saving.value = true;
    try {
      const result = await createCommissionWithdrawal(payload);
      if (result.code !== 0) return toast.error(result.message || "提现申请失败");
      toast.success("提现申请已提交");
      withdrawalOpen.value = false;
      await Promise.all([loadOverview(), loadPage(transactions, getCommissionTransactions), loadPage(withdrawals, getCommissionWithdrawals)]);
    } finally {
      saving.value = false;
    }
  }

  return {
    overview,
    downlines,
    transactions,
    withdrawals,
    withdrawalOpen,
    saving,
    loadAll,
    updateRate,
    submitWithdrawal,
    changeDownlinesPage: (delta) => changePage(downlines, getDistributionDownlines, delta),
    changeTransactionsPage: (delta) => changePage(transactions, getCommissionTransactions, delta),
    changeWithdrawalsPage: (delta) => changePage(withdrawals, getCommissionWithdrawals, delta),
  };
}
