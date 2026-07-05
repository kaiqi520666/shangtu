<script setup>
import { onMounted } from "vue";
import AdminHeygenAvatarsPanel from "@/components/admin/heygen/AdminHeygenAvatarsPanel.vue";
import HeygenResourceEditorModal from "@/components/admin/heygen/HeygenResourceEditorModal.vue";
import { useAdminHeygenAvatars } from "@/composables/admin/useAdminHeygenAvatars.js";

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
} = useAdminHeygenAvatars();

onMounted(() => {
  loadItems();
});
</script>

<template>
  <AdminHeygenAvatarsPanel
    :state="state"
    :syncing="syncing"
    @apply-filter="applyFilter"
    @change-page="changePage"
    @edit="openEditModal"
    @toggle="toggleItem"
    @sync="syncItems"
  />
  <HeygenResourceEditorModal
    :open="editorOpen"
    :form="form"
    :saving="editorSaving"
    title="编辑系统数字人"
    enabled-label="启用数字人"
    @close="closeEditor"
    @submit="saveItem"
  />
</template>
