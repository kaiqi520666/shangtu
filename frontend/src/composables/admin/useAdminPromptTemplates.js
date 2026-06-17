import { reactive, ref } from "vue";
import {
  createAdminPromptTemplate,
  getAdminPromptTemplates,
  updateAdminPromptTemplate,
} from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";

const emptyForm = {
  id: "",
  scenario: "",
  purpose: "image_generate",
  platform: "",
  type_id: "",
  model: "gpt-image-2",
  name: "",
  content: "",
  version: 1,
  active: true,
};

export function useAdminPromptTemplates() {
  const toast = useToast();
  const { loadPage, applyFilter: applyPageFilter, changePage: changeAdminPage } = useAdminPageLoader(toast);
  const state = reactive(createAdminPageState({
    scenario: "",
    purpose: "",
    model: "",
    active: "",
  }));
  const editorOpen = ref(false);
  const editorSaving = ref(false);
  const form = reactive({ ...emptyForm });

  async function loadTemplates() {
    await loadPage(
      state,
      getAdminPromptTemplates,
      {
        scenario: state.scenario || undefined,
        purpose: state.purpose || undefined,
        model: state.model || undefined,
        active: state.active || undefined,
      },
      "加载提示词模板失败",
    );
  }

  function applyFilter() {
    applyPageFilter(state, loadTemplates);
  }

  function changePage(direction) {
    changeAdminPage(state, loadTemplates, direction);
  }

  function openCreateModal() {
    Object.assign(form, { ...emptyForm });
    editorOpen.value = true;
  }

  function openEditModal(template) {
    Object.assign(form, {
      id: template.id,
      scenario: template.scenario || "",
      purpose: template.purpose || "image_generate",
      platform: template.platform || "",
      type_id: template.type_id || "",
      model: template.model || "gpt-image-2",
      name: template.name || "",
      content: template.content || "",
      version: template.version || 1,
      active: Boolean(template.active),
    });
    editorOpen.value = true;
  }

  function closeEditor() {
    editorOpen.value = false;
  }

  async function saveTemplate(formPayload = form) {
    const payload = {
      scenario: formPayload.scenario || null,
      purpose: formPayload.purpose,
      platform: formPayload.platform || null,
      type_id: formPayload.type_id || null,
      model: String(formPayload.model || "").trim(),
      name: String(formPayload.name || "").trim(),
      content: String(formPayload.content || "").trim(),
      version: Number(formPayload.version || 1),
      active: Boolean(formPayload.active),
    };
    if (!payload.name || !payload.content || !payload.purpose || !payload.model) {
      toast.error("请填写名称、用途、模型和提示词内容");
      return;
    }

    editorSaving.value = true;
    try {
      const templateId = formPayload.id || form.id;
      const result = templateId
        ? await updateAdminPromptTemplate(templateId, payload)
        : await createAdminPromptTemplate(payload);
      if (result.code !== 0) {
        toast.error(result.message || "保存提示词模板失败");
        return;
      }
      toast.success("提示词模板已保存");
      editorOpen.value = false;
      await loadTemplates();
    } catch {
      toast.error("保存提示词模板失败");
    } finally {
      editorSaving.value = false;
    }
  }

  async function toggleTemplate(template) {
    try {
      const result = await updateAdminPromptTemplate(template.id, {
        scenario: template.scenario || null,
        purpose: template.purpose,
        platform: template.platform || null,
        type_id: template.type_id || null,
        model: template.model,
        name: template.name,
        content: template.content,
        version: Number(template.version || 1),
        active: !template.active,
      });
      if (result.code !== 0) {
        toast.error(result.message || "更新提示词模板失败");
        return;
      }
      toast.success(template.active ? "提示词模板已停用" : "提示词模板已启用");
      await loadTemplates();
    } catch {
      toast.error("更新提示词模板失败");
    }
  }

  return {
    state,
    form,
    editorOpen,
    editorSaving,
    loadTemplates,
    applyFilter,
    changePage,
    openCreateModal,
    openEditModal,
    closeEditor,
    saveTemplate,
    toggleTemplate,
  };
}
