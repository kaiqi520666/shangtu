<script setup>
import { computed } from 'vue'
import { BadgeCheck, Image, Layers3, ListChecks, Minus, Plus, Search } from 'lucide-vue-next'
import AppCheckbox from '@/components/ui/AppCheckbox.vue'

const props = defineProps({
  structure: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['update:structure'])

const totalCount = computed(() =>
  props.structure.reduce((sum, item) => {
    if (!item.enabled) return sum
    return sum + item.count
  }, 0),
)

const iconMap = {
  'white-bg': Image,
  scene: Layers3,
  'selling-point': BadgeCheck,
  detail: Search,
}

function updateItem(index, patch) {
  emit(
    'update:structure',
    props.structure.map((item, currentIndex) => {
      if (currentIndex !== index) return item
      return {
        ...item,
        ...patch,
      }
    }),
  )
}

function toggleItem(index) {
  const current = props.structure[index]
  if (!current) return
  updateItem(index, { enabled: !current.enabled })
}

function changeCount(index, step) {
  const current = props.structure[index]
  if (!current) return
  const nextCount = Math.min(current.maxCount, Math.max(1, current.count + step))
  updateItem(index, { count: nextCount, enabled: true })
}
</script>

<template>
  <section class="space-y-3 border-b border-slate-100 p-5">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <ListChecks class="h-4 w-4" />
        </span>
        <div>
          <h3 class="text-xs font-bold text-slate-900">套图结构配置</h3>
          <p class="text-xs text-slate-400">勾选需要生成的图片类型和张数</p>
        </div>
      </div>
      <span class="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-bold text-primary">
        共 {{ totalCount }} 张
      </span>
    </div>

    <div class="space-y-2.5">
      <article
        v-for="(item, index) in structure"
        :key="item.id"
        class="rounded-2xl border p-3 transition-all"
        :class="item.enabled ? 'border-primary/25 bg-primary/5' : 'border-slate-200 bg-white'"
      >
        <div class="flex items-center gap-3">
          <AppCheckbox :model-value="item.enabled" @change="toggleItem(index)" />

          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
            :class="item.enabled ? 'bg-white text-primary shadow-sm' : 'bg-slate-100 text-slate-400'"
          >
            <component :is="iconMap[item.id]" class="h-4.5 w-4.5" />
          </span>

          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between gap-3">
              <div class="min-w-0">
                <h4 class="text-sm font-bold text-slate-900">{{ item.name }}</h4>
                <p class="mt-1 text-xs leading-relaxed text-slate-500">{{ item.description }}</p>
              </div>
              <div
                v-if="item.enabled"
                class="flex shrink-0 items-center rounded-lg border border-slate-200 bg-white p-0.5 shadow-sm"
              >
                <button
                  type="button"
                  class="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
                  :disabled="item.count <= 1"
                  @click="changeCount(index, -1)"
                >
                  <Minus class="h-3.5 w-3.5" />
                </button>
                <span class="w-7 text-center text-xs font-black text-slate-800">{{ item.count }}</span>
                <button
                  type="button"
                  class="flex h-7 w-7 items-center justify-center rounded-md text-primary transition-colors hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-40"
                  :disabled="item.count >= item.maxCount"
                  @click="changeCount(index, 1)"
                >
                  <Plus class="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
