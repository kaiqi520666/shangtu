<script setup>
import { Search } from "lucide-vue-next";

defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  placeholder: {
    type: String,
    default: "搜索",
  },
});

const emit = defineEmits(["update:modelValue", "search"]);
</script>

<template>
  <div class="flex min-w-64 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
    <Search class="h-4 w-4 shrink-0 text-slate-300" />
    <input
      :value="modelValue"
      type="text"
      class="w-full border-0 bg-transparent text-xs outline-none"
      :placeholder="placeholder"
      @input="emit('update:modelValue', $event.target.value)"
      @keyup.enter="emit('search')"
    />
  </div>
</template>
