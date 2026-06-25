import { reactive, ref } from "vue";
import {
  getAdminProductCatalog,
  updateAdminProductCatalog,
} from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";
import { useCatalogStore } from "@/stores/catalog.js";

const emptyForm = {
  id: "",
  scenario: "",
  item_id: "",
  name: "",
  description: "",
  strategy: "",
  default_count: null,
  max_count: null,
  enabled: true,
  sort: 0,
};

export function useAdminProductCatalog() {
  const toast = useToast();
  const catalog = useCatalogStore();
  const { loadPage, applyFilter: applyPageFilter, changePage: changeAdminPage } = useAdminPageLoader(toast);
  const state = reactive(createAdminPageState({
    scenario: "",
    enabled: "",
  }));
  const editorOpen = ref(false);
  const editorSaving = ref(false);
  const form = reactive({ ...emptyForm });

  async function loadCatalogItems() {
    await loadPage(
      state,
      getAdminProductCatalog,
      {
        scenario: state.scenario || undefined,
        enabled: state.enabled || undefined,
      },
      "加载商品目录失败",
    );
  }

  function applyFilter() {
    applyPageFilter(state, loadCatalogItems);
  }

  function changePage(direction) {
    changeAdminPage(state, loadCatalogItems, direction);
  }

  function openEditModal(item) {
    Object.assign(form, {
      id: item.id,
      scenario: item.scenario || "",
      item_id: item.item_id || "",
      name: item.name || "",
      description: item.description || "",
      strategy: item.strategy || "",
      default_count: item.default_count ?? null,
      max_count: item.max_count ?? null,
      enabled: Boolean(item.enabled),
      sort: Number(item.sort || 0),
    });
    editorOpen.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
  }

  async function saveCatalogItem(formPayload) {
    const payload = normalizePayload(formPayload);
    if (!payload) return;

    editorSaving.value = true;
    try {
      const result = await updateAdminProductCatalog(formPayload.id, payload);
      if (result.code !== 0) {
        toast.error(result.message || "保存商品目录失败");
        return;
      }
      toast.success("商品目录已保存");
      editorOpen.value = false;
      await refreshRuntimeCatalog();
      await loadCatalogItems();
    } catch {
      toast.error("保存商品目录失败");
    } finally {
      editorSaving.value = false;
    }
  }

  async function toggleCatalogItem(item) {
    const payload = normalizePayload({
      ...item,
      enabled: !item.enabled,
    });
    if (!payload) return;

    try {
      const result = await updateAdminProductCatalog(item.id, payload);
      if (result.code !== 0) {
        toast.error(result.message || "更新商品目录失败");
        return;
      }
      toast.success(item.enabled ? "目录项已停用" : "目录项已启用");
      await refreshRuntimeCatalog();
      await loadCatalogItems();
    } catch {
      toast.error("更新商品目录失败");
    }
  }

  function normalizePayload(formPayload) {
    const name = String(formPayload.name || "").trim();
    const description = String(formPayload.description || "").trim();
    const strategy = String(formPayload.strategy || "").trim();
    if (!name || !description || !strategy) {
      toast.error("请填写名称、展示描述和生成策略");
      return null;
    }

    const payload = {
      name,
      description,
      strategy,
      enabled: Boolean(formPayload.enabled),
      sort: Number(formPayload.sort || 0),
      default_count: null,
      max_count: null,
    };

    if (formPayload.scenario === "product_suite") {
      payload.default_count = Number(formPayload.default_count || 1);
      payload.max_count = Number(formPayload.max_count || 1);
      if (payload.default_count > payload.max_count) {
        toast.error("默认张数不能大于最大张数");
        return null;
      }
    }

    return payload;
  }

  async function refreshRuntimeCatalog() {
    try {
      await catalog.reload();
    } catch {
      toast.info("目录已更新，生成页刷新后会读取最新配置");
    }
  }

  return {
    state,
    form,
    editorOpen,
    editorSaving,
    loadCatalogItems,
    applyFilter,
    changePage,
    openEditModal,
    closeEditor,
    saveCatalogItem,
    toggleCatalogItem,
  };
}
