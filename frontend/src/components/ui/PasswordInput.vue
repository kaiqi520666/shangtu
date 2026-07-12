<script setup>
import { ref } from "vue";
import { Eye, EyeOff, Lock } from "lucide-vue-next";

defineProps({
  modelValue: { type: String, default: "" },
  label: { type: String, required: true },
  autocomplete: { type: String, required: true },
  placeholder: { type: String, default: "请输入密码" },
});

const emit = defineEmits(["update:modelValue"]);
const visible = ref(false);
</script>

<template>
  <label class="block">
    <span class="mb-1.5 block text-xs font-bold text-slate-600">{{ label }}</span>
    <span class="flex h-11 items-center rounded-xl border border-slate-200 bg-white px-3 transition-colors focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/15">
      <Lock class="h-4 w-4 shrink-0 text-slate-400" />
      <input
        :value="modelValue"
        :type="visible ? 'text' : 'password'"
        :autocomplete="autocomplete"
        :placeholder="placeholder"
        class="min-w-0 flex-1 bg-transparent px-2.5 text-sm font-semibold text-slate-800 outline-none placeholder:font-medium placeholder:text-slate-400"
        @input="emit('update:modelValue', $event.target.value)"
      />
      <button
        type="button"
        class="flex h-8 w-8 shrink-0 items-center justify-center text-slate-400 hover:text-slate-600"
        :title="visible ? '隐藏密码' : '显示密码'"
        @click="visible = !visible"
      >
        <EyeOff v-if="visible" class="h-4 w-4" />
        <Eye v-else class="h-4 w-4" />
      </button>
    </span>
  </label>
</template>
