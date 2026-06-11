<script setup>
import GlobalToast from '@/components/GlobalToast.vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
</script>

<template>
  <DefaultLayout>
    <RouterView />
    <GlobalToast />
  </DefaultLayout>
</template>
