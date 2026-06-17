import { totalPages } from "@/constants/admin.js";

export function createAdminPageState(extra = {}) {
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

export function useAdminPageLoader(toast) {
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

  function applyFilter(state, loader) {
    state.page = 1;
    loader();
  }

  function changePage(state, loader, direction) {
    const nextPage = state.page + direction;
    if (nextPage < 1 || nextPage > totalPages(state)) return;
    state.page = nextPage;
    loader();
  }

  return {
    loadPage,
    applyFilter,
    changePage,
  };
}
