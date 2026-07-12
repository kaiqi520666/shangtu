<script setup>
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";
import { BadgeDollarSign, CreditCard, HandCoins, UserRound } from "lucide-vue-next";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import AppTabNav from "@/components/ui/AppTabNav.vue";
import { useAuthStore } from "@/stores/auth.js";

const route = useRoute();
const authStore = useAuthStore();

const accountTabs = computed(() => [
  { key: "profile", label: "账号中心", to: "/account/profile" },
  { key: "credits", label: "积分明细", to: "/account/credits" },
  { key: "pricing", label: "计费标准", to: "/account/pricing" },
  ...(authStore.distributionEnabled ? [{ key: "distribution", label: "分销中心", to: "/account/distribution" }] : []),
]);

const tabIcons = {
  profile: UserRound,
  credits: CreditCard,
  pricing: BadgeDollarSign,
  distribution: HandCoins,
};

const activeTab = computed(() => accountTabs.value.find((tab) => tab.to === route.path)?.key || "profile");
</script>

<template>
  <GeneratorLayout>
    <div class="flex flex-1 flex-col overflow-hidden">
      <header class="border-b border-slate-200 bg-white px-6 py-4">
        <h1 class="text-base font-black text-slate-900">账号中心</h1>
        <p class="mt-1 text-xs text-slate-500">账号、积分与计费信息</p>
      </header>

      <div class="border-b border-slate-200 bg-white px-6">
        <AppTabNav :tabs="accountTabs" :active-key="activeTab" :icons="tabIcons" />
      </div>

      <main class="flex-1 overflow-y-auto bg-slate-50 p-6">
        <RouterView />
      </main>
    </div>
  </GeneratorLayout>
</template>
