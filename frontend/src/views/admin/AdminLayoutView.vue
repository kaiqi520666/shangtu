<script setup>
import {
  Images,
  LayoutDashboard,
  MessageSquareText,
  PackageSearch,
  ReceiptText,
  HandCoins,
  RefreshCw,
  ScrollText,
  Settings,
  ShoppingBag,
  TicketPercent,
  Languages,
  Volume2,
  UserRoundCheck,
  UsersRound,
} from "lucide-vue-next";
import { computed, ref } from "vue";
import { RouterView, useRoute } from "vue-router";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import AppTabNav from "@/components/ui/AppTabNav.vue";
import { adminTabs } from "@/constants/admin.js";

const route = useRoute();
const refreshKey = ref(0);
const activeTab = computed(() => adminTabs.find((tab) => tab.to === route.path)?.key || "overview");
const tabIcons = {
  overview: LayoutDashboard,
  users: UsersRound,
  orders: ShoppingBag,
  transactions: ReceiptText,
  couponCodes: TicketPercent,
  commissionWithdrawals: HandCoins,
  imageTasks: Images,
  assets: Images,
  settings: Settings,
  productCatalog: PackageSearch,
  promptTemplates: MessageSquareText,
  outfitModels: UserRoundCheck,
  heygenAvatars: UserRoundCheck,
  heygenVoices: Volume2,
  heygenTranslationLanguages: Languages,
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
        <AppTabNav :tabs="adminTabs" :active-key="activeTab" :icons="tabIcons" />
      </div>

      <main class="flex-1 overflow-y-auto p-6">
        <RouterView :key="`${route.fullPath}-${refreshKey}`" />
      </main>
    </div>
  </GeneratorLayout>
</template>
