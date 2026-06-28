<script setup>
import { onMounted } from "vue";
import AdminSettingsPanel from "@/components/admin/settings/AdminSettingsPanel.vue";
import { useAdminSettings } from "@/composables/admin/useAdminSettings.js";

const {
  settingsState,
  loadSettings,
  saveSettings,
  addRechargePackage,
  removeRechargePackage,
} = useAdminSettings();

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
