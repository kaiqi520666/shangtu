<script setup>
import { onMounted } from "vue";
import AdminHeygenTranslationLanguagesPanel from "@/components/admin/heygen/AdminHeygenTranslationLanguagesPanel.vue";
import HeygenTranslationLanguageEditorModal from "@/components/admin/heygen/HeygenTranslationLanguageEditorModal.vue";
import { useAdminHeygenTranslationLanguages } from "@/composables/admin/useAdminHeygenTranslationLanguages.js";

const {
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
} = useAdminHeygenTranslationLanguages();

onMounted(() => {
  loadItems();
});
</script>

<template>
  <AdminHeygenTranslationLanguagesPanel
    :state="state"
    :syncing="syncing"
    @apply-filter="applyFilter"
    @change-page="changePage"
    @edit="openEditModal"
    @toggle="toggleItem"
    @sync="syncItems"
  />
  <HeygenTranslationLanguageEditorModal
    :open="editorOpen"
    :form="form"
    :saving="editorSaving"
    @close="closeEditor"
    @submit="saveItem"
  />
</template>
