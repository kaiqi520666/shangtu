<script setup>
import { onMounted } from "vue";
import AdminAssetsPanel from "@/components/admin/assets/AdminAssetsPanel.vue";
import { useAdminAssets } from "@/composables/admin/useAdminAssets.js";

const controller = useAdminAssets();

onMounted(controller.loadAssets);
</script>

<template>
  <AdminAssetsPanel
    :state="controller.state"
    :all-selected="controller.allSelected.value"
    :selected-count="controller.selectedCardsCount.value"
    :downloading="controller.downloading.value"
    :preview="controller.zoomCard.value"
    :scenario-label="controller.scenarioLabel"
    :meta-label="controller.metaLabel"
    @query="controller.applyAssetsFilter"
    @change-scenario="controller.changeScenario"
    @toggle-all="controller.toggleSelectAllCards"
    @toggle-card="controller.toggleCardSelection"
    @download="controller.downloadSingleMedia"
    @batch-download="controller.batchDownload"
    @preview="controller.zoomCard.value = $event"
    @change-page="controller.changePage"
    @close-preview="controller.zoomCard.value = null"
  />
</template>
