<script setup>
import { onMounted } from "vue";
import AdminImageTasksPanel from "@/components/admin/AdminImageTasksPanel.vue";
import { useAdminDashboard } from "@/composables/useAdminDashboard.js";

const { imageTasksState, loadImageTasks, applyImageTasksFilter, changePage } = useAdminDashboard();

onMounted(() => {
  loadImageTasks();
});
</script>

<template>
  <AdminImageTasksPanel
    :state="imageTasksState"
    @apply-filter="applyImageTasksFilter"
    @change-page="changePage(imageTasksState, loadImageTasks, $event)"
  />
</template>
