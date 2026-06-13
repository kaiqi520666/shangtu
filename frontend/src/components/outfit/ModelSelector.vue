<script setup>
import { Check, ImagePlus } from 'lucide-vue-next'

defineProps({
  models: {
    type: Array,
    required: true,
  },
  selectedId: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:selectedId'])
</script>

<template>
  <section class="space-y-3 border-b border-slate-100 p-5">
    <h3 class="text-xs font-bold text-slate-900">模特形象</h3>
    <div class="grid grid-cols-4 gap-2">
      <button
        type="button"
        class="flex aspect-square flex-col items-center justify-center rounded-xl bg-slate-100 text-slate-400 transition-colors hover:bg-slate-200/70"
      >
        <ImagePlus class="h-5 w-5" />
        <span class="mt-1 text-xs">上传新模特</span>
      </button>
      <div
        v-if="loading"
        class="col-span-3 flex aspect-[3/1] items-center justify-center rounded-xl bg-slate-50 text-xs font-semibold text-slate-400"
      >
        正在加载模特...
      </div>
      <div
        v-else-if="models.length === 0"
        class="col-span-3 flex aspect-[3/1] items-center justify-center rounded-xl bg-slate-50 text-xs font-semibold text-slate-400"
      >
        暂无可用模特
      </div>
      <template v-else>
        <button
          v-for="model in models"
          :key="model.id"
          type="button"
          class="group relative aspect-square overflow-hidden rounded-xl border bg-slate-100 transition-all"
          :class="selectedId === model.id ? 'border-primary ring-2 ring-primary/10' : 'border-transparent hover:border-slate-200'"
          :title="model.name"
          @click="emit('update:selectedId', model.id)"
        >
          <img :src="model.image" class="h-full w-full object-cover transition-transform group-hover:scale-105" :alt="model.name" />
          <span
            v-if="selectedId === model.id"
            class="absolute left-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded bg-primary text-white"
          >
            <Check class="h-3 w-3 stroke-[3]" />
          </span>
        </button>
      </template>
    </div>
  </section>
</template>
