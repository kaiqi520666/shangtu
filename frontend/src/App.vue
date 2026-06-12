<script setup>
import GlobalConfirm from '@/components/GlobalConfirm.vue'
import GlobalToast from '@/components/GlobalToast.vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
</script>

<template>
  <DefaultLayout>
    <RouterView />
    <GlobalToast />
    <GlobalConfirm />
  </DefaultLayout>
</template>
