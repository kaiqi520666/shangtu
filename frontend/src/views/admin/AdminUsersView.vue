<script setup>
import { onMounted } from "vue";
import AdjustCreditsModal from "@/components/admin/users/AdjustCreditsModal.vue";
import AdminUsersPanel from "@/components/admin/users/AdminUsersPanel.vue";
import { useAdminUsers } from "@/composables/admin/useAdminUsers.js";

const {
  usersState,
  adjustModalOpen,
  adjustTarget,
  adjustSaving,
  loadUsers,
  applyUsersFilter,
  changeUserRole,
  changeUserStatus,
  openAdjustModal,
  closeAdjustModal,
  submitAdjustCredits,
  changePage,
} = useAdminUsers();

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
    :saving="adjustSaving"
    @close="closeAdjustModal"
    @submit="submitAdjustCredits"
  />
</template>
