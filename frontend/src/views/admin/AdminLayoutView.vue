<script setup>
import {
  Images,
  LayoutDashboard,
  MessageSquareText,
  PackageSearch,
  ReceiptText,
  RefreshCw,
  ScrollText,
  Settings,
  ShoppingBag,
  UserRoundCheck,
  UsersRound,
} from "lucide-vue-next";
import { computed, ref } from "vue";
import { RouterView, useRoute } from "vue-router";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import { adminTabs } from "@/constants/admin.js";

const route = useRoute();
const refreshKey = ref(0);
const activeTab = computed(() => adminTabs.find((tab) => tab.to === route.path)?.key || "overview");
const tabIcons = {
  overview: LayoutDashboard,
  users: UsersRound,
  orders: ShoppingBag,
  transactions: ReceiptText,
  imageTasks: Images,
  settings: Settings,
  productCatalog: PackageSearch,
  promptTemplates: MessageSquareText,
  outfitModels: UserRoundCheck,
  auditLogs: ScrollText,
};

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

      <div class="border-b border-slate-200 bg-white px-6">
        <nav class="flex gap-1.5 overflow-x-auto py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <RouterLink
            v-for="tab in adminTabs"
            :key="tab.key"
            :to="tab.to"
            class="group relative flex h-9 shrink-0 items-center gap-2 rounded-lg border px-3 text-xs font-bold transition-colors"
            :class="
              activeTab === tab.key
                ? 'border-primary/20 bg-primary/10 text-primary'
                : 'border-transparent text-slate-500 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-800'
            "
          >
            <component
              :is="tabIcons[tab.key]"
              class="h-3.5 w-3.5"
              :class="activeTab === tab.key ? 'text-primary' : 'text-slate-400 group-hover:text-slate-600'"
            />
            {{ tab.label }}
            <span
              v-if="activeTab === tab.key"
              class="absolute inset-x-3 -bottom-2 h-0.5 rounded-full bg-primary"
            ></span>
          </RouterLink>
        </nav>
      </div>

      <main class="flex-1 overflow-y-auto p-6">
        <RouterView :key="`${route.fullPath}-${refreshKey}`" />
      </main>
    </div>
  </GeneratorLayout>
</template>
