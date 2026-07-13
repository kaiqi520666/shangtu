<script setup>
import { onMounted, ref } from "vue";
import AdminNamedResourceModal from "@/components/admin/common/AdminNamedResourceModal.vue";
import AdminHeygenAvatarsPanel from "@/components/admin/heygen/AdminHeygenAvatarsPanel.vue";
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
const previewOpen = ref(false);
const previewItem = ref(null);

onMounted(() => {
  loadItems();
});
</script>

<template>
  <AdminHeygenAvatarsPanel
    :state="state"
    :syncing="syncing"
    v-model:preview-open="previewOpen"
    v-model:preview-item="previewItem"
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
    title="编辑系统数字人"
    enabled-label="启用数字人"
    @close="closeEditor"
    @submit="saveItem"
  />
</template>
