<script setup>
import AppPagination from "@/components/ui/AppPagination.vue";

defineProps({
  state: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["change-page"]);
</script>

<template>
  <AppPagination :state="state" @change-page="emit('change-page', $event)" />
</template>
