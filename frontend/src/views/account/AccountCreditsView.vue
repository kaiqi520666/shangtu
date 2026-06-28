<script setup>
import { computed, onMounted } from "vue";
import { ArrowDownLeft, ArrowUpRight, ReceiptText } from "lucide-vue-next";
import AppPagination from "@/components/ui/AppPagination.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { useAccountTransactions } from "@/composables/account/useAccountTransactions.js";
import { formatTime, transactionTypeLabel, transactionTypeOptions } from "@/constants/admin.js";
import { useAuthStore } from "@/stores/auth.js";

const authStore = useAuthStore();
const { state, loadTransactions, applyFilter, changePage } = useAccountTransactions();

const transactionSummary = computed(() => {
  const income = state.items
    .filter((item) => Number(item.credits_delta || 0) > 0)
    .reduce((sum, item) => sum + Number(item.credits_delta || 0), 0);
  const outcome = state.items
    .filter((item) => Number(item.credits_delta || 0) < 0)
    .reduce((sum, item) => sum + Math.abs(Number(item.credits_delta || 0)), 0);
  return { income, outcome };
});

function deltaClass(delta) {
  return Number(delta || 0) >= 0 ? "text-emerald-600" : "text-rose-600";
}

onMounted(() => {
  loadTransactions();
});
</script>

<template>
  <section class="mx-auto max-w-6xl space-y-5">
    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p class="text-xs font-bold text-slate-500">当前积分</p>
        <p class="mt-2 text-3xl font-black text-slate-950">{{ authStore.credits }} <span class="text-sm text-slate-400">点</span></p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
          <ArrowDownLeft class="h-4 w-4 text-emerald-600" />
          本页收入
        </div>
        <p class="mt-2 text-2xl font-black text-emerald-600">+{{ transactionSummary.income }}</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="flex items-center gap-2 text-xs font-bold text-slate-500">
          <ArrowUpRight class="h-4 w-4 text-rose-600" />
          本页消耗
        </div>
        <p class="mt-2 text-2xl font-black text-rose-600">-{{ transactionSummary.outcome }}</p>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
        <div class="flex items-center gap-2 text-sm font-black text-slate-900">
          <ReceiptText class="h-4 w-4 text-slate-400" />
          积分明细
        </div>
        <div class="ml-auto w-36">
          <AppSelect v-model="state.type" :options="transactionTypeOptions" @update:model-value="applyFilter" />
        </div>
        <span class="text-xs font-semibold text-slate-400">共 {{ state.total }} 条</span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 text-slate-400">
            <tr>
              <th class="px-4 py-3 font-semibold">时间</th>
              <th class="px-4 py-3 font-semibold">类型</th>
              <th class="px-4 py-3 font-semibold">积分变动</th>
              <th class="px-4 py-3 font-semibold">变动后余额</th>
              <th class="px-4 py-3 font-semibold">说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="state.loading">
              <td colspan="5" class="px-4 py-12 text-center text-slate-400">正在加载积分明细...</td>
            </tr>
            <tr v-else-if="!state.items.length">
              <td colspan="5" class="px-4 py-12 text-center text-slate-400">暂无积分明细</td>
            </tr>
            <tr v-for="tx in state.items" v-else :key="tx.id" class="border-t border-slate-100">
              <td class="whitespace-nowrap px-4 py-3 text-slate-500">{{ formatTime(tx.created_at) }}</td>
              <td class="px-4 py-3 font-bold text-slate-700">{{ transactionTypeLabel(tx.type) }}</td>
              <td class="px-4 py-3 text-sm font-black" :class="deltaClass(tx.credits_delta)">
                {{ tx.credits_delta >= 0 ? "+" : "" }}{{ tx.credits_delta }}
              </td>
              <td class="px-4 py-3 font-bold text-slate-800">{{ tx.balance_after }} 点</td>
              <td class="min-w-64 px-4 py-3 text-slate-500">{{ tx.note || "-" }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="border-t border-slate-100 p-4">
        <AppPagination :state="state" @change-page="changePage" />
      </div>
    </div>
  </section>
</template>
