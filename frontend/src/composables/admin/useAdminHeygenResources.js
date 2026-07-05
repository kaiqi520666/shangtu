import { reactive, ref } from "vue";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";

const emptyForm = {
  id: "",
  name: "",
  sort_order: 0,
  enabled: true,
};

export function useAdminHeygenResources({
  listApi,
  updateApi,
  syncApi,
  loadErrorMessage,
  saveErrorMessage,
  syncErrorMessage,
  saveSuccessMessage,
  syncSuccessMessage,
  enabledOnMessage,
  enabledOffMessage,
  nameRequiredMessage,
}) {
  const toast = useToast();
  const { loadPage, applyFilter: applyPageFilter, changePage: changeAdminPage } = useAdminPageLoader(toast);
  const state = reactive(createAdminPageState({
    active: "",
  }));
  const editorOpen = ref(false);
  const editorSaving = ref(false);
  const syncing = ref(false);
  const form = reactive({ ...emptyForm });

  async function loadItems() {
    await loadPage(
      state,
      listApi,
      {
        active: state.active || undefined,
      },
      loadErrorMessage,
    );
  }

  function applyFilter() {
    applyPageFilter(state, loadItems);
  }

  function changePage(direction) {
    changeAdminPage(state, loadItems, direction);
  }

  function openEditModal(item) {
    Object.assign(form, {
      id: item.id,
      name: item.name || "",
      sort_order: Number(item.sort_order || 0),
      enabled: Boolean(item.enabled),
    });
    editorOpen.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
  }

  async function saveItem(formPayload) {
    const name = String(formPayload.name || "").trim();
    if (!name) {
      toast.error(nameRequiredMessage);
      return;
    }

    editorSaving.value = true;
    try {
      const result = await updateApi(formPayload.id, {
        name,
        sort_order: Number(formPayload.sort_order || 0),
        enabled: Boolean(formPayload.enabled),
      });
      if (result.code !== 0) {
        toast.error(result.message || saveErrorMessage);
        return;
      }
      toast.success(saveSuccessMessage);
      editorOpen.value = false;
      await loadItems();
    } catch {
      toast.error(saveErrorMessage);
    } finally {
      editorSaving.value = false;
    }
  }

  async function toggleItem(item) {
    try {
      const result = await updateApi(item.id, {
        enabled: !item.enabled,
      });
      if (result.code !== 0) {
        toast.error(result.message || saveErrorMessage);
        return;
      }
      toast.success(item.enabled ? enabledOffMessage : enabledOnMessage);
      await loadItems();
    } catch {
      toast.error(saveErrorMessage);
    }
  }

  async function syncItems() {
    syncing.value = true;
    try {
      const result = await syncApi();
      if (result.code !== 0) {
        toast.error(result.message || syncErrorMessage);
        return;
      }
      toast.success(syncSuccessMessage);
      await loadItems();
    } catch {
      toast.error(syncErrorMessage);
    } finally {
      syncing.value = false;
    }
  }

  return {
    state,
    form,
    editorOpen,
    editorSaving,
    syncing,
    loadItems,
    applyFilter,
    changePage,
    openEditModal,
    closeEditor,
    saveItem,
    toggleItem,
    syncItems,
  };
}
