<script setup>
import GeneratorHeader from '@/components/GeneratorHeader.vue'
import GeneratorSidebar from '@/components/GeneratorSidebar.vue'
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-slate-50 text-slate-800">
    <GeneratorHeader />
    <div class="flex flex-1 overflow-hidden">
      <GeneratorSidebar />
      <main class="flex flex-1 overflow-hidden">
        <slot />
      </main>
    </div>
  </div>
</template>
