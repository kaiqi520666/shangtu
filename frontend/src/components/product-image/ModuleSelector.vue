<script setup>
import AppCheckbox from '@/components/ui/AppCheckbox.vue'

const props = defineProps({
  modules: {
    type: Array,
    required: true,
  },
  selected: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['update:selected'])

function toggleModule(id) {
  if (props.selected.includes(id)) {
    emit(
      'update:selected',
      props.selected.filter((item) => item !== id),
    )
  } else {
    emit('update:selected', [...props.selected, id])
  }
}

function toggleAll(enabled) {
  emit('update:selected', enabled ? props.modules.map((module) => module.id) : [])
}
</script>

<template>
  <section class="flex-1 space-y-3 bg-slate-50/20 p-5">
    <div class="flex items-center justify-between">
      <label class="text-xs font-bold text-slate-500">选择生成图种类型 ({{ selected.length }}项)</label>
      <div class="flex gap-2">
        <button type="button" class="text-xs font-semibold text-slate-400 hover:text-primary" @click="toggleAll(true)">全选</button>
        <span class="text-xs text-slate-300">|</span>
        <button type="button" class="text-xs font-semibold text-slate-400 hover:text-slate-600" @click="toggleAll(false)">取消</button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-2 pb-6">
      <article
        v-for="module in modules"
        :key="module.id"
        class="flex h-20 cursor-pointer flex-col justify-between rounded-xl border p-2.5 text-left shadow-sm transition-all duration-200"
        :class="
          selected.includes(module.id)
            ? 'border-primary/40 bg-primary/10 text-slate-950 ring-1 ring-primary/10'
            : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50/50'
        "
        @click="toggleModule(module.id)"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="truncate text-xs font-bold" :class="selected.includes(module.id) ? 'text-primary' : 'text-slate-700'">{{ module.name }}</span>
          <AppCheckbox
            :model-value="selected.includes(module.id)"
            size="sm"
            @change="toggleModule(module.id)"
          />
        </div>
        <p class="mt-1 line-clamp-2 text-xs leading-normal" :class="selected.includes(module.id) ? 'text-primary' : 'text-slate-400'">
          {{ module.desc }}
        </p>
      </article>
    </div>
  </section>
</template>
