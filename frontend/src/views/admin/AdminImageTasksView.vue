<script setup>
import { onMounted } from "vue";
import AdminImageTasksPanel from "@/components/admin/AdminImageTasksPanel.vue";
import { useAdminImageTasks } from "@/composables/admin/useAdminImageTasks.js";

const { imageTasksState, loadImageTasks, applyImageTasksFilter, changePage } = useAdminImageTasks();

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
