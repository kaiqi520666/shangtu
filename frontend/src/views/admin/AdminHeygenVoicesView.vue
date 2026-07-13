<script setup>
import { onMounted } from "vue";
import AdminNamedResourceModal from "@/components/admin/common/AdminNamedResourceModal.vue";
import AdminHeygenVoicesPanel from "@/components/admin/heygen/AdminHeygenVoicesPanel.vue";
import { useAdminHeygenVoices } from "@/composables/admin/useAdminHeygenVoices.js";

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
} = useAdminHeygenVoices();

onMounted(() => {
  loadItems();
});
</script>

<template>
  <AdminHeygenVoicesPanel
    :state="state"
    :syncing="syncing"
    @apply-filter="applyFilter"
    @change-page="changePage"
    @edit="openEditModal"
    @toggle="toggleItem"
    @sync="syncItems"
  />
  <AdminNamedResourceModal
    :open="editorOpen"
    :form="form"
    :saving="editorSaving"
    title="编辑系统声音"
    enabled-label="启用声音"
    @close="closeEditor"
    @submit="saveItem"
  />
</template>
