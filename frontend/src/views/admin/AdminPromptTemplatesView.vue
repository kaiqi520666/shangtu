<script setup>
import { onMounted } from "vue";
import AdminPromptTemplatesPanel from "@/components/admin/AdminPromptTemplatesPanel.vue";
import PromptTemplateEditorModal from "@/components/admin/PromptTemplateEditorModal.vue";
import { useAdminPromptTemplates } from "@/composables/admin/useAdminPromptTemplates.js";

const {
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
} = useAdminPromptTemplates();

onMounted(() => {
  loadTemplates();
});
</script>

<template>
  <AdminPromptTemplatesPanel
    :state="state"
    @apply-filter="applyFilter"
    @change-page="changePage"
    @create="openCreateModal"
    @edit="openEditModal"
    @toggle="toggleTemplate"
  />
  <PromptTemplateEditorModal
    :open="editorOpen"
    :form="form"
    :saving="editorSaving"
    @close="closeEditor"
    @submit="saveTemplate"
  />
</template>
