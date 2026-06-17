import { reactive } from "vue";
import { getAdminCreditOrders } from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";

const ordersState = reactive(createAdminPageState({ status: "" }));

export function useAdminOrders() {
  const toast = useToast();
  const { loadPage, applyFilter, changePage } = useAdminPageLoader(toast);

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

  function applyOrdersFilter() {
    applyFilter(ordersState, loadOrders);
  }

  return {
    ordersState,
    loadOrders,
    applyOrdersFilter,
    changePage,
  };
}
