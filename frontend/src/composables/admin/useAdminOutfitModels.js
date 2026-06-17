import { reactive, ref } from "vue";
import {
  getAdminOutfitModels,
  updateAdminOutfitModel,
  uploadAdminOutfitModel,
} from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

export function useAdminOutfitModels() {
  const confirm = useConfirm();
  const toast = useToast();
  const { loadPage, applyFilter: applyPageFilter, changePage: changeAdminPage } = useAdminPageLoader(toast);
  const state = reactive(createAdminPageState({
    active: "",
  }));
  const editorOpen = ref(false);
  const editorSaving = ref(false);
  const uploadSaving = ref(false);
  const uploadResetKey = ref(0);
  const form = reactive({
    id: "",
    name: "",
    sort_order: 0,
    active: true,
  });

  async function loadModels() {
    await loadPage(
      state,
      getAdminOutfitModels,
      {
        active: state.active || undefined,
      },
      "加载系统模特失败",
    );
  }

  function applyFilter() {
    applyPageFilter(state, loadModels);
  }

  function changePage(direction) {
    changeAdminPage(state, loadModels, direction);
  }

  function openEditModal(model) {
    Object.assign(form, {
      id: model.id,
      name: model.name || "",
      sort_order: Number(model.sort_order || 0),
      active: Boolean(model.active),
    });
    editorOpen.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
  }

  async function uploadModel(payload) {
    if (!payload?.file) {
      toast.error("请选择模特图片");
      return;
    }
    uploadSaving.value = true;
    try {
      const result = await uploadAdminOutfitModel({
        file: payload.file,
        name: String(payload.name || "").trim(),
        sortOrder: payload.sortOrder,
      });
      if (result.code !== 0) {
        toast.error(result.message || "上传系统模特失败");
        return;
      }
      toast.success("系统模特已上传");
      uploadResetKey.value += 1;
      await loadModels();
    } catch {
      toast.error("上传系统模特失败");
    } finally {
      uploadSaving.value = false;
    }
  }

  async function saveModel(formPayload = form) {
    const modelName = String(formPayload.name || "").trim();
    if (!modelName) {
      toast.error("请填写模特名称");
      return;
    }
    editorSaving.value = true;
    try {
      const result = await updateAdminOutfitModel(formPayload.id || form.id, {
        name: modelName,
        sort_order: Number(formPayload.sort_order || 0),
        active: Boolean(formPayload.active),
      });
      if (result.code !== 0) {
        toast.error(result.message || "保存系统模特失败");
        return;
      }
      toast.success("系统模特已保存");
      editorOpen.value = false;
      await loadModels();
    } catch {
      toast.error("保存系统模特失败");
    } finally {
      editorSaving.value = false;
    }
  }

  async function toggleModel(model) {
    try {
      const result = await updateAdminOutfitModel(model.id, { active: !model.active });
      if (result.code !== 0) {
        toast.error(result.message || "更新系统模特失败");
        return;
      }
      toast.success(model.active ? "系统模特已停用" : "系统模特已启用");
      await loadModels();
    } catch {
      toast.error("更新系统模特失败");
    }
  }

  async function deleteModel(model) {
    const ok = await confirm.open({
      title: "停用系统模特",
      message: `确定停用「${model.name}」吗？用户将不再看到这个系统模特。`,
      confirmText: "停用",
      cancelText: "取消",
      tone: "danger",
    });
    if (!ok) return;
    try {
      const result = await updateAdminOutfitModel(model.id, { active: false });
      if (result.code !== 0) {
        toast.error(result.message || "停用系统模特失败");
        return;
      }
      toast.success("系统模特已停用");
      await loadModels();
    } catch {
      toast.error("停用系统模特失败");
    }
  }

  return {
    state,
    form,
    editorOpen,
    editorSaving,
    uploadSaving,
    uploadResetKey,
    loadModels,
    applyFilter,
    changePage,
    openEditModal,
    closeEditor,
    uploadModel,
    saveModel,
    toggleModel,
    deleteModel,
  };
}
