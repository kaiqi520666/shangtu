<script setup>
import AppModal from "@/components/ui/AppModal.vue";
import AppTabNav from "@/components/ui/AppTabNav.vue";

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: "",
  },
  tabs: {
    type: Array,
    required: true,
  },
  activeTab: {
    type: String,
    required: true,
  },
  keyword: {
    type: String,
    default: "",
  },
  searchPlaceholder: {
    type: String,
    default: "搜索",
  },
  summary: {
    type: String,
    default: "",
  },
  showToolbar: {
    type: Boolean,
    default: true,
  },
  loadingMore: {
    type: Boolean,
    default: false,
  },
  panelClass: {
    type: String,
    default: "h-[85vh] w-full max-w-6xl",
  },
});

const emit = defineEmits([
  "close",
  "change-tab",
  "update:keyword",
  "search",
  "reach-end",
]);

function handleScroll(event) {
  emit("reach-end", event);
}
</script>

<template>
  <AppModal :open="open" :title="title" :subtitle="subtitle" :panel-class="panelClass" @close="emit('close')">
    <div class="flex min-h-0 flex-1 flex-col">
      <div class="border-b border-slate-100 p-4">
        <AppTabNav :tabs="tabs" :active-key="activeTab" @change="emit('change-tab', $event)" />

        <div v-if="showToolbar" class="mt-3 flex flex-wrap items-center gap-2">
          <input
            :value="keyword"
            type="text"
            class="min-w-72 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
            :placeholder="searchPlaceholder"
            @input="emit('update:keyword', $event.target.value)"
            @keyup.enter="emit('search')"
          />
          <slot name="filters" />
          <button type="button" class="rounded-xl bg-primary px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-secondary" @click="emit('search')">查询</button>
          <span v-if="summary" class="ml-auto text-xs text-slate-400">{{ summary }}</span>
        </div>
      </div>

      <div class="min-h-0 flex-1 overflow-y-auto p-4" @scroll.passive="handleScroll">
        <slot />

        <div v-if="loadingMore" class="flex items-center justify-center py-4 text-xs text-slate-400">
          正在加载更多...
        </div>
      </div>

      <div v-if="$slots.footer" class="shrink-0 border-t border-slate-100 bg-white p-4">
        <slot name="footer" />
      </div>
    </div>
  </AppModal>
</template>
