import { reactive } from "vue";
import { getAdminCreditTransactions } from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";

const transactionsState = reactive(createAdminPageState({ type: "" }));

export function useAdminTransactions() {
  const toast = useToast();
  const { loadPage, applyFilter, changePage } = useAdminPageLoader(toast);

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

  function applyTransactionsFilter() {
    applyFilter(transactionsState, loadTransactions);
  }

  return {
    transactionsState,
    loadTransactions,
    applyTransactionsFilter,
    changePage,
  };
}
