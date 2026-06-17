<script setup>
import { onMounted } from "vue";
import AdminOutfitModelsPanel from "@/components/admin/AdminOutfitModelsPanel.vue";
import OutfitModelEditorModal from "@/components/admin/OutfitModelEditorModal.vue";
import { useAdminOutfitModels } from "./composables/useAdminOutfitModels.js";

const {
  state,
  form,
  uploadForm,
  editorOpen,
  editorSaving,
  uploadSaving,
  loadModels,
  applyFilter,
  changePage,
  openEditModal,
  closeEditor,
  setUploadFile,
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
    :upload-form="uploadForm"
    :upload-saving="uploadSaving"
    @apply-filter="applyFilter"
    @change-page="changePage"
    @file-change="setUploadFile"
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
