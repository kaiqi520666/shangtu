<script setup>
import { LoaderCircle } from "lucide-vue-next";

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  empty: {
    type: Boolean,
    default: false,
  },
  colspan: {
    type: Number,
    required: true,
  },
  emptyText: {
    type: String,
    default: "暂无数据",
  },
});
</script>

<template>
  <tr v-if="loading || empty">
    <td :colspan="colspan" class="px-4 py-10 text-center text-slate-400">
      <LoaderCircle v-if="loading" class="mx-auto mb-2 h-5 w-5 animate-spin" />
      {{ loading ? "加载中..." : emptyText }}
    </td>
  </tr>
</template>
