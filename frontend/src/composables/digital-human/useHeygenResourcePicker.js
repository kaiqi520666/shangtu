import { reactive } from "vue";

export function useHeygenResourcePicker({
  listApi,
  defaultFilters = {},
  buildParams,
  pageSize = 24,
}) {
  const initialFilters = { ...defaultFilters };
  const state = reactive({
    items: [],
    total: 0,
    page: 1,
    pageSize,
    keyword: "",
    loading: false,
    loadingMore: false,
    initialized: false,
    finished: false,
  });
  const filters = reactive({ ...initialFilters });

  function resetFilters() {
    state.keyword = "";
    Object.assign(filters, initialFilters);
  }

  function resetList() {
    state.items = [];
    state.total = 0;
    state.page = 1;
    state.initialized = false;
    state.finished = false;
  }

  function reset() {
    resetFilters();
    resetList();
  }

  async function load({ append = false } = {}) {
    if (append ? state.loadingMore : state.loading) {
      return { ok: true };
    }
    if (append && state.finished) {
      return { ok: true };
    }

    if (append) {
      state.loadingMore = true;
    } else {
      state.loading = true;
    }

    try {
      const result = await listApi(
        buildParams({
          page: state.page,
          pageSize: state.pageSize,
          keyword: state.keyword,
          filters,
        }),
      );
      if (result.code !== 0) {
        if (!append) {
          state.items = [];
          state.total = 0;
          state.finished = true;
        }
        return { ok: false, message: result.message || "加载失败" };
      }

      const data = result.data || {};
      const nextItems = Array.isArray(data.items) ? data.items : [];
      state.total = Number(data.total || 0);
      state.items = append ? [...state.items, ...nextItems] : nextItems;
      state.initialized = true;
      state.finished = state.items.length >= state.total || nextItems.length < state.pageSize;
      return { ok: true };
    } catch (error) {
      if (!append) {
        state.items = [];
        state.total = 0;
        state.finished = true;
      }
      return {
        ok: false,
        message: error.response?.data?.message || "加载失败",
      };
    } finally {
      state.loading = false;
      state.loadingMore = false;
    }
  }

  async function reload() {
    state.page = 1;
    state.finished = false;
    return load();
  }

  async function loadMore() {
    if (state.loading || state.loadingMore || state.finished) {
      return { ok: true };
    }
    state.page += 1;
    const result = await load({ append: true });
    if (!result.ok) {
      state.page -= 1;
    }
    return result;
  }

  function handleScroll(event) {
    const element = event?.target;
    if (!element) return Promise.resolve({ ok: true });
    const distanceToBottom = element.scrollHeight - element.scrollTop - element.clientHeight;
    if (distanceToBottom <= 120) {
      return loadMore();
    }
    return Promise.resolve({ ok: true });
  }

  return {
    state,
    filters,
    reset,
    reload,
    loadMore,
    handleScroll,
  };
}
