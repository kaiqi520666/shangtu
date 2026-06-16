<script setup>
import { onMounted } from "vue";
import AdjustCreditsModal from "@/components/admin/AdjustCreditsModal.vue";
import AdminUsersPanel from "@/components/admin/AdminUsersPanel.vue";
import { useAdminDashboard } from "@/composables/useAdminDashboard.js";

const {
  usersState,
  adjustModalOpen,
  adjustTarget,
  adjustSaving,
  adjustForm,
  loadUsers,
  applyUsersFilter,
  changeUserRole,
  changeUserStatus,
  openAdjustModal,
  closeAdjustModal,
  submitAdjustCredits,
  changePage,
} = useAdminDashboard();

onMounted(() => {
  loadUsers();
});
</script>

<template>
  <AdminUsersPanel
    :state="usersState"
    @apply-filter="applyUsersFilter"
    @adjust-credits="openAdjustModal"
    @change-role="changeUserRole"
    @change-status="changeUserStatus"
    @change-page="changePage(usersState, loadUsers, $event)"
  />
  <AdjustCreditsModal
    :open="adjustModalOpen"
    :target="adjustTarget"
    :form="adjustForm"
    :saving="adjustSaving"
    @close="closeAdjustModal"
    @submit="submitAdjustCredits"
  />
</template>
