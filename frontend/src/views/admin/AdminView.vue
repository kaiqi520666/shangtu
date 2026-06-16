<script setup>
import { onMounted, ref, watch } from "vue";
import { RefreshCw } from "lucide-vue-next";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import AdjustCreditsModal from "./components/AdjustCreditsModal.vue";
import AdminOrdersPanel from "./components/AdminOrdersPanel.vue";
import AdminOverviewPanel from "./components/AdminOverviewPanel.vue";
import AdminTransactionsPanel from "./components/AdminTransactionsPanel.vue";
import AdminUsersPanel from "./components/AdminUsersPanel.vue";
import { useAdminDashboard } from "./composables/useAdminDashboard.js";

const tabs = [
  { key: "overview", label: "概览" },
  { key: "users", label: "用户" },
  { key: "orders", label: "订单" },
  { key: "transactions", label: "流水" },
];

const activeTab = ref("overview");

const {
  overviewCards,
  overviewLoading,
  usersState,
  ordersState,
  transactionsState,
  adjustModalOpen,
  adjustTarget,
  adjustSaving,
  adjustForm,
  loadOverview,
  loadUsers,
  loadOrders,
  loadTransactions,
  applyUsersFilter,
  applyOrdersFilter,
  applyTransactionsFilter,
  changeUserRole,
  changeUserStatus,
  openAdjustModal,
  closeAdjustModal,
  submitAdjustCredits,
  changePage,
} = useAdminDashboard();

function loadActiveTab() {
  if (activeTab.value === "overview") loadOverview();
  if (activeTab.value === "users") loadUsers();
  if (activeTab.value === "orders") loadOrders();
  if (activeTab.value === "transactions") loadTransactions();
}

watch(activeTab, () => {
  loadActiveTab();
});

onMounted(() => {
  loadOverview();
});
</script>

<template>
  <GeneratorLayout>
    <div class="flex flex-1 flex-col overflow-hidden">
      <header class="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div>
          <h1 class="text-base font-bold text-slate-800">管理后台</h1>
          <p class="text-xs text-slate-400">用户、充值订单和积分流水管理</p>
        </div>
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          @click="loadActiveTab"
        >
          <RefreshCw class="h-3.5 w-3.5" />
          刷新
        </button>
      </header>

      <div class="border-b border-slate-200 bg-white px-6 pt-3">
        <nav class="flex w-fit gap-1 rounded-lg bg-slate-100 p-0.5">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            class="rounded-md px-4 py-1.5 text-xs font-bold transition-all"
            :class="activeTab === tab.key ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <main class="flex-1 overflow-y-auto p-6">
        <AdminOverviewPanel
          v-if="activeTab === 'overview'"
          :cards="overviewCards"
          :loading="overviewLoading"
        />
        <AdminUsersPanel
          v-else-if="activeTab === 'users'"
          :state="usersState"
          @apply-filter="applyUsersFilter"
          @adjust-credits="openAdjustModal"
          @change-role="changeUserRole"
          @change-status="changeUserStatus"
          @change-page="changePage(usersState, loadUsers, $event)"
        />
        <AdminOrdersPanel
          v-else-if="activeTab === 'orders'"
          :state="ordersState"
          @apply-filter="applyOrdersFilter"
          @change-page="changePage(ordersState, loadOrders, $event)"
        />
        <AdminTransactionsPanel
          v-else
          :state="transactionsState"
          @apply-filter="applyTransactionsFilter"
          @change-page="changePage(transactionsState, loadTransactions, $event)"
        />
      </main>

      <AdjustCreditsModal
        :open="adjustModalOpen"
        :target="adjustTarget"
        :form="adjustForm"
        :saving="adjustSaving"
        @close="closeAdjustModal"
        @submit="submitAdjustCredits"
      />
    </div>
  </GeneratorLayout>
</template>
