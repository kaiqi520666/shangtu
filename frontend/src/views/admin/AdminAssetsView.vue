<script setup>
import { onMounted } from "vue";
import AdminAssetsPanel from "@/components/admin/assets/AdminAssetsPanel.vue";
import { useAdminAssets } from "@/composables/admin/useAdminAssets.js";

const controller = useAdminAssets();

onMounted(controller.loadAssets);
</script>

<template>
  <AdminAssetsPanel :controller="controller" />
</template>
