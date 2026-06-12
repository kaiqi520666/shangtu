<script setup>
import GlobalConfirm from '@/components/ui/GlobalConfirm.vue'
import GlobalToast from '@/components/ui/GlobalToast.vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
</script>

<template>
  <DefaultLayout>
    <RouterView />
    <GlobalToast />
    <GlobalConfirm />
  </DefaultLayout>
</template>
