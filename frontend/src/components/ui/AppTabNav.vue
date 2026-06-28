<script setup>
defineProps({
  tabs: {
    type: Array,
    required: true,
  },
  activeKey: {
    type: [String, Number],
    default: "",
  },
  icons: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(["change"])
</script>

<template>
  <nav class="flex gap-1.5 overflow-x-auto py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
    <component
      :is="tab.to ? 'RouterLink' : 'button'"
      v-for="tab in tabs"
      :key="tab.key ?? tab.value"
      :to="tab.to"
      :type="tab.to ? undefined : 'button'"
      class="group relative flex h-9 shrink-0 items-center gap-2 rounded-lg border px-3 text-xs font-bold transition-colors"
      :class="
        activeKey === (tab.key ?? tab.value)
          ? 'border-primary/20 bg-primary/10 text-primary'
          : 'border-transparent text-slate-500 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-800'
      "
      @click="!tab.to && emit('change', tab.value)"
    >
      <component
        :is="icons[tab.key ?? tab.value]"
        v-if="icons[tab.key ?? tab.value]"
        class="h-3.5 w-3.5"
        :class="activeKey === (tab.key ?? tab.value) ? 'text-primary' : 'text-slate-400 group-hover:text-slate-600'"
      />
      {{ tab.label }}
      <span
        v-if="activeKey === (tab.key ?? tab.value)"
        class="absolute inset-x-3 -bottom-2 h-0.5 rounded-full bg-primary"
      ></span>
    </component>
  </nav>
</template>
