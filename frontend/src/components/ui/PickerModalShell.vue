<script setup>
import AppModal from "@/components/ui/AppModal.vue";
import AppTabNav from "@/components/ui/AppTabNav.vue";

defineProps({
  open: { type: Boolean, default: false }, title: { type: String, required: true }, subtitle: { type: String, default: "" },
  tabs: { type: Array, default: () => [] }, activeTab: { type: String, default: "" }, keyword: { type: String, default: "" },
  searchPlaceholder: { type: String, default: "搜索" }, summary: { type: String, default: "" }, showToolbar: { type: Boolean, default: true },
  loadingMore: { type: Boolean, default: false }, panelClass: { type: String, default: "h-[85vh] w-full max-w-6xl" },
});
const emit = defineEmits(["close", "change-tab", "update:keyword", "search", "reach-end"]);
</script>

<template>
  <AppModal :open="open" :title="title" :subtitle="subtitle" :panel-class="panelClass" @close="emit('close')">
    <div class="flex min-h-0 flex-1 flex-col">
      <div v-if="tabs.length || showToolbar" class="border-b border-slate-100 p-4">
        <AppTabNav v-if="tabs.length" :tabs="tabs" :active-key="activeTab" @change="emit('change-tab', $event)" />
        <div v-if="showToolbar" class="flex flex-wrap items-center gap-2" :class="tabs.length ? 'mt-3' : ''">
          <input :value="keyword" type="text" class="min-w-72 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs outline-none focus:border-primary" :placeholder="searchPlaceholder" @input="emit('update:keyword', $event.target.value)" @keyup.enter="emit('search')" />
          <slot name="filters" />
          <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white hover:bg-secondary" @click="emit('search')">查询</button>
          <span v-if="summary" class="ml-auto text-xs text-slate-400">{{ summary }}</span>
        </div>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto p-4" @scroll.passive="emit('reach-end', $event)"><slot /><div v-if="loadingMore" class="py-4 text-center text-xs text-slate-400">正在加载更多...</div></div>
      <div v-if="$slots.footer" class="shrink-0 border-t border-slate-100 bg-white p-4"><slot name="footer" /></div>
    </div>
  </AppModal>
</template>
