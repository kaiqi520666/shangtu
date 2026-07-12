<script setup>
import { onMounted } from "vue";
import AdjustCreditsModal from "@/components/admin/users/AdjustCreditsModal.vue";
import AdminUsersPanel from "@/components/admin/users/AdminUsersPanel.vue";
import ResetUserPasswordModal from "@/components/admin/users/ResetUserPasswordModal.vue";
import UserBusinessSettingsModal from "@/components/admin/users/UserBusinessSettingsModal.vue";
import { useAdminUsers } from "@/composables/admin/useAdminUsers.js";

const {
  usersState,
  adjustModalOpen,
  adjustTarget,
  adjustSaving,
  businessModalOpen,
  businessTarget,
  businessSaving,
  passwordReset,
  loadUsers,
  applyUsersFilter,
  changeUserRole,
  changeUserStatus,
  openAdjustModal,
  closeAdjustModal,
  submitAdjustCredits,
  openBusinessModal,
  closeBusinessModal,
  submitBusinessSettings,
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
    @business-settings="openBusinessModal"
    @reset-password="passwordReset.show"
    @change-role="changeUserRole"
    @change-status="changeUserStatus"
    @change-page="changePage(usersState, loadUsers, $event)"
  />
  <UserBusinessSettingsModal :open="businessModalOpen" :target="businessTarget" :saving="businessSaving" @close="closeBusinessModal" @submit="submitBusinessSettings" />
  <AdjustCreditsModal
    :open="adjustModalOpen"
    :target="adjustTarget"
    :saving="adjustSaving"
    @close="closeAdjustModal"
    @submit="submitAdjustCredits"
  />
  <ResetUserPasswordModal
    :open="passwordReset.open.value"
    :target="passwordReset.target.value"
    :saving="passwordReset.saving.value"
    @close="passwordReset.open.value = false"
    @submit="passwordReset.submit"
  />
</template>
