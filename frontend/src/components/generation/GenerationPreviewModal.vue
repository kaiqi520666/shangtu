<script setup>
import AppModal from '@/components/ui/AppModal.vue'

defineProps({
  card: {
    type: Object,
    default: null,
  },
  title: {
    type: String,
    required: true,
  },
  alt: {
    type: String,
    default: '生成图片预览',
  },
})

const emit = defineEmits(['close'])
</script>

<template>
  <AppModal
    :open="Boolean(card)"
    :title="title"
    panel-class="w-full max-w-4xl"
    @close="emit('close')"
  >
    <div v-if="card" class="bg-slate-100 p-6">
      <img :src="card.dataUrl" class="mx-auto max-h-[75vh] rounded-xl object-contain shadow-lg" :alt="alt" />
    </div>
  </AppModal>
</template>
