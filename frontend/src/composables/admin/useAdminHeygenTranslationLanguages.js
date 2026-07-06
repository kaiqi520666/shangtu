import { reactive, ref } from "vue";
import {
  getAdminHeygenTranslationLanguages,
  syncAdminHeygenTranslationLanguages,
  updateAdminHeygenTranslationLanguage,
} from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";

const emptyForm = {
  id: "",
  name: "",
  display_name_zh: "",
  sort_order: 0,
  enabled: true,
};

export function useAdminHeygenTranslationLanguages() {
  const toast = useToast();
  const { loadPage, applyFilter: applyPageFilter, changePage: changeAdminPage } = useAdminPageLoader(toast);
  const state = reactive(createAdminPageState({ active: "" }));
  const editorOpen = ref(false);
  const editorSaving = ref(false);
  const syncing = ref(false);
  const form = reactive({ ...emptyForm });

  async function loadItems() {
    await loadPage(
      state,
      getAdminHeygenTranslationLanguages,
      { active: state.active || undefined },
      "加载翻译语言失败",
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
      display_name_zh: item.display_name_zh || "",
      sort_order: Number(item.sort_order || 0),
      enabled: Boolean(item.enabled),
    });
    editorOpen.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
  }

  async function saveItem(formPayload) {
    const displayNameZh = String(formPayload.display_name_zh || "").trim();
    if (!displayNameZh) {
      toast.error("请填写中文展示名");
      return;
    }
    editorSaving.value = true;
    try {
      const result = await updateAdminHeygenTranslationLanguage(formPayload.id, {
        display_name_zh: displayNameZh,
        sort_order: Number(formPayload.sort_order || 0),
        enabled: Boolean(formPayload.enabled),
      });
      if (result.code !== 0) {
        toast.error(result.message || "保存翻译语言失败");
        return;
      }
      toast.success("翻译语言已保存");
      editorOpen.value = false;
      await loadItems();
    } catch {
      toast.error("保存翻译语言失败");
    } finally {
      editorSaving.value = false;
    }
  }

  async function toggleItem(item) {
    try {
      const result = await updateAdminHeygenTranslationLanguage(item.id, {
        enabled: !item.enabled,
      });
      if (result.code !== 0) {
        toast.error(result.message || "保存翻译语言失败");
        return;
      }
      toast.success(item.enabled ? "翻译语言已停用" : "翻译语言已启用");
      await loadItems();
    } catch {
      toast.error("保存翻译语言失败");
    }
  }

  async function syncItems() {
    syncing.value = true;
    try {
      const result = await syncAdminHeygenTranslationLanguages();
      if (result.code !== 0) {
        toast.error(result.message || "同步翻译语言失败");
        return;
      }
      toast.success("HeyGen 翻译语言已同步");
      await loadItems();
    } catch {
      toast.error("同步翻译语言失败");
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
