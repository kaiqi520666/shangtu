<script setup>
import { onMounted } from "vue";
import AdminProductCatalogPanel from "@/components/admin/catalog/AdminProductCatalogPanel.vue";
import ProductCatalogEditorModal from "@/components/admin/catalog/ProductCatalogEditorModal.vue";
import { useAdminProductCatalog } from "@/composables/admin/useAdminProductCatalog.js";

const {
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
} = useAdminProductCatalog();

onMounted(() => {
  loadCatalogItems();
});
</script>

<template>
  <AdminProductCatalogPanel
    :state="state"
    @apply-filter="applyFilter"
    @change-page="changePage"
    @edit="openEditModal"
    @toggle="toggleCatalogItem"
  />
  <ProductCatalogEditorModal
    :open="editorOpen"
    :form="form"
    :saving="editorSaving"
    @close="closeEditor"
    @submit="saveCatalogItem"
  />
</template>
