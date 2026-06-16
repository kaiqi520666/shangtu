<script setup>
import { RefreshCw } from "lucide-vue-next";
import { computed, ref } from "vue";
import { RouterView, useRoute } from "vue-router";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import { adminTabs } from "@/constants/admin.js";

const route = useRoute();
const refreshKey = ref(0);
const activeTab = computed(() => adminTabs.find((tab) => tab.to === route.path)?.key || "overview");

function refreshCurrentView() {
  refreshKey.value += 1;
}
</script>

<template>
  <GeneratorLayout>
    <div class="flex flex-1 flex-col overflow-hidden">
      <header class="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div>
          <h1 class="text-base font-bold text-slate-800">管理后台</h1>
          <p class="text-xs text-slate-400">用户、订单、任务、配置和审计管理</p>
        </div>
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          @click="refreshCurrentView"
        >
          <RefreshCw class="h-3.5 w-3.5" />
          刷新
        </button>
      </header>

      <div class="border-b border-slate-200 bg-white px-6 pt-3">
        <nav class="flex w-fit gap-1 rounded-lg bg-slate-100 p-0.5">
          <RouterLink
            v-for="tab in adminTabs"
            :key="tab.key"
            :to="tab.to"
            class="rounded-md px-4 py-1.5 text-xs font-bold transition-all"
            :class="activeTab === tab.key ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'"
          >
            {{ tab.label }}
          </RouterLink>
        </nav>
      </div>

      <main class="flex-1 overflow-y-auto p-6">
        <RouterView :key="`${route.fullPath}-${refreshKey}`" />
      </main>
    </div>
  </GeneratorLayout>
</template>
