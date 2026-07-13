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
import { RouterLink, RouterView, useRoute } from "vue-router";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import AppTabNav from "@/components/ui/AppTabNav.vue";
import { adminMenuGroups } from "@/constants/admin.js";

const route = useRoute();
const refreshKey = ref(0);
const activeGroup = computed(() => adminMenuGroups.find((group) => group.items.some((item) => item.to === route.path)) || adminMenuGroups[0]);
const activeTab = computed(() => activeGroup.value.items.find((item) => item.to === route.path)?.key || activeGroup.value.items[0].key);
const groupIcons = {
  overview: LayoutDashboard,
  finance: UsersRound,
  content: PackageSearch,
  capabilities: UserRoundCheck,
  system: Settings,
};
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
        <nav aria-label="后台一级导航" class="flex gap-6 overflow-x-auto py-2.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <RouterLink
            v-for="group in adminMenuGroups"
            :key="group.key"
            :to="group.items[0].to"
            class="flex h-9 shrink-0 items-center gap-2 border-b-2 px-1 text-xs font-black transition-colors"
            :class="activeGroup.key === group.key ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800'"
          >
            <component :is="groupIcons[group.key]" class="h-4 w-4" />
            {{ group.label }}
          </RouterLink>
        </nav>
      </div>
      <div aria-label="后台二级导航" class="border-b border-slate-200 bg-slate-50/80 px-6">
        <AppTabNav :tabs="activeGroup.items" :active-key="activeTab" :icons="tabIcons" />
      </div>

      <main class="flex-1 overflow-y-auto p-6">
        <RouterView :key="`${route.fullPath}-${refreshKey}`" />
      </main>
    </div>
  </GeneratorLayout>
</template>
