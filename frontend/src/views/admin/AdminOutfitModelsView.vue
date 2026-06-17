<script setup>
import { onMounted } from "vue";
import AdminOutfitModelsPanel from "@/components/admin/AdminOutfitModelsPanel.vue";
import OutfitModelEditorModal from "@/components/admin/OutfitModelEditorModal.vue";
import { useAdminOutfitModels } from "./composables/useAdminOutfitModels.js";

const {
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
} = useAdminOutfitModels();

onMounted(() => {
  loadModels();
});
</script>

<template>
  <AdminOutfitModelsPanel
    :state="state"
    :upload-saving="uploadSaving"
    :upload-reset-key="uploadResetKey"
    @apply-filter="applyFilter"
    @change-page="changePage"
    @upload="uploadModel"
    @edit="openEditModal"
    @toggle="toggleModel"
    @delete="deleteModel"
  />
  <OutfitModelEditorModal
    :open="editorOpen"
    :form="form"
    :saving="editorSaving"
    @close="closeEditor"
    @submit="saveModel"
  />
</template>
