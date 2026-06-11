<script setup>
import { Check } from 'lucide-vue-next'

const props = defineProps({
  scenes: {
    type: Array,
    required: true,
  },
  selected: {
    type: Array,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:selected', 'update:description'])

function toggleScene(id) {
  if (props.selected.includes(id)) {
    emit(
      'update:selected',
      props.selected.filter((item) => item !== id),
    )
  } else {
    emit('update:selected', [...props.selected, id])
  }
}
</script>

<template>
  <section class="space-y-3 border-b border-slate-100 p-5">
    <h3 class="text-xs font-bold text-slate-900">拍摄场景</h3>
    <div class="grid grid-cols-3 gap-2">
      <button
        v-for="scene in scenes"
        :key="scene.id"
        type="button"
        class="flex items-center gap-2 rounded-xl border px-3 py-2.5 text-left text-xs font-semibold transition-all"
        :class="
          selected.includes(scene.id)
            ? 'border-primary/40 bg-primary/10 text-primary'
            : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300 hover:bg-white'
        "
        @click="toggleScene(scene.id)"
      >
        <span
          class="flex h-4 w-4 shrink-0 items-center justify-center rounded border"
          :class="selected.includes(scene.id) ? 'border-primary bg-primary text-white' : 'border-slate-300 bg-white'"
        >
          <Check v-if="selected.includes(scene.id)" class="h-3 w-3 stroke-[3]" />
        </span>
        {{ scene.label }}
      </button>
    </div>

    <div class="space-y-1.5">
      <label class="block text-xs font-bold text-slate-500">或自定义描述场景（可选）</label>
      <textarea
        :value="description"
        rows="3"
        class="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
        placeholder="描述你想要的场景：如秋季枫叶小径、暖色调午后阳光、模特倚靠树干..."
        @input="emit('update:description', $event.target.value)"
      ></textarea>
    </div>
  </section>
</template>
