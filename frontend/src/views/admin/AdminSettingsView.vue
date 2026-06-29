<script setup>
import { onMounted } from "vue";
import AdminSettingsPanel from "@/components/admin/settings/AdminSettingsPanel.vue";
import { useAdminSettings } from "@/composables/admin/useAdminSettings.js";
import { useConfirm } from "@/composables/useConfirm.js";

const {
  settingsState,
  loadSettings,
  saveSettings,
  addRechargePackage,
  removeRechargePackage,
} = useAdminSettings();
const confirm = useConfirm();

onMounted(() => {
  loadSettings();
});

async function handleRemoveRechargePackage(index) {
  const pkg = settingsState.rechargePackages[index];
  const label = pkg?.name || `${pkg?.credits || ""}积分套餐`;
  const ok = await confirm.open({
    title: "删除充值套餐",
    message: `确定删除「${label}」吗？需要点击保存后才会生效。`,
    confirmText: "删除",
    cancelText: "取消",
    tone: "danger",
  });
  if (!ok) return;
  removeRechargePackage(index);
}
</script>

<template>
  <AdminSettingsPanel
    :state="settingsState"
    @save="saveSettings"
    @add-package="addRechargePackage"
    @remove-package="handleRemoveRechargePackage"
  />
</template>
