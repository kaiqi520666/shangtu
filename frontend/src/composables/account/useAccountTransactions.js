import { reactive } from "vue";
import { getAccountCreditTransactions } from "@/api/account.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";

export function createAccountPageState(extra = {}) {
  return {
    items: [],
    total: 0,
    page: 1,
    pageSize: 20,
    loading: false,
    ...extra,
  };
}

export function useAccountTransactions() {
  const toast = useToast();
  const state = reactive(createAccountPageState({ type: "" }));

  async function loadTransactions() {
    state.loading = true;
    try {
      const result = await getAccountCreditTransactions({
        page: state.page,
        page_size: state.pageSize,
        type: state.type || undefined,
      });
      if (result.code !== 0) {
        toast.error(result.message || "加载积分明细失败");
        return;
      }
      state.items = result.data?.items || [];
      state.total = Number(result.data?.total || 0);
      state.page = Number(result.data?.page || state.page);
      state.pageSize = Number(result.data?.page_size || state.pageSize);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "加载积分明细失败"));
    } finally {
      state.loading = false;
    }
  }

  function applyFilter() {
    state.page = 1;
    loadTransactions();
  }

  function changePage(delta) {
    const next = state.page + delta;
    const totalPages = Math.max(1, Math.ceil(Number(state.total || 0) / Number(state.pageSize || 20)));
    if (next < 1 || next > totalPages) return;
    state.page = next;
    loadTransactions();
  }

  return {
    state,
    loadTransactions,
    applyFilter,
    changePage,
  };
}
