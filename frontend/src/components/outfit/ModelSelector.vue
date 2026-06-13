<script setup>
import { computed, ref } from 'vue'
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

const hoveredModel = ref(null)
const previewPosition = ref({ top: 96, left: 460 })

const previewStyle = computed(() => ({
  top: `${previewPosition.value.top}px`,
  left: `${previewPosition.value.left}px`,
}))

function showPreview(model, event) {
  hoveredModel.value = model
  updatePreviewPosition(event)
}

function updatePreviewPosition(event) {
  const gap = 16
  const width = 240
  const height = 320
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  let left = event.clientX + gap
  if (left + width > viewportWidth - gap) {
    left = event.clientX - width - gap
  }

  let top = event.clientY - height / 2
  top = Math.max(gap, Math.min(top, viewportHeight - height - gap))

  previewPosition.value = { top, left: Math.max(gap, left) }
}

function hidePreview() {
  hoveredModel.value = null
}
</script>

<template>
  <section class="space-y-3 border-b border-slate-100 p-5">
    <h3 class="text-xs font-bold text-slate-900">模特形象</h3>
    <div class="max-h-[324px] overflow-y-auto pr-1 [scrollbar-width:thin]">
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
            @mouseenter="showPreview(model, $event)"
            @mousemove="updatePreviewPosition"
            @mouseleave="hidePreview"
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
    </div>

    <Teleport to="body">
      <div
        v-if="hoveredModel"
        class="pointer-events-none fixed z-[80] hidden w-[240px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/20 md:block"
        :style="previewStyle"
      >
        <img
          :src="hoveredModel.image"
          class="h-[320px] w-full object-cover"
          :alt="hoveredModel.name"
        />
      </div>
    </Teleport>
  </section>
</template>
