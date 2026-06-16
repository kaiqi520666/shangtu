<script setup>
import { onMounted } from "vue";
import AdminSettingsPanel from "@/components/admin/AdminSettingsPanel.vue";
import { useAdminDashboard } from "@/composables/useAdminDashboard.js";

const {
  settingsState,
  loadSettings,
  saveSettings,
  addRechargePackage,
  removeRechargePackage,
} = useAdminDashboard();

onMounted(() => {
  loadSettings();
});
</script>

<template>
  <AdminSettingsPanel
    :state="settingsState"
    @save="saveSettings"
    @add-package="addRechargePackage"
    @remove-package="removeRechargePackage"
  />
</template>
