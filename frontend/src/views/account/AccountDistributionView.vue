<script setup>
import { onMounted, ref } from "vue";
import DistributionDownlines from "@/components/distribution/DistributionDownlines.vue";
import DistributionSummary from "@/components/distribution/DistributionSummary.vue";
import WithdrawalModal from "@/components/distribution/WithdrawalModal.vue";
import AppPagination from "@/components/ui/AppPagination.vue";
import { useDistributionCenter } from "@/composables/account/useDistributionCenter.js";
import { formatMoney, formatTime } from "@/constants/admin.js";

const distribution = useDistributionCenter();
const tab = ref("downlines");
const tabs = [{ key: "downlines", label: "下级用户" }, { key: "transactions", label: "佣金流水" }, { key: "withdrawals", label: "提现记录" }];
const withdrawalStatus = { pending_review: "待审核", pending_payment: "待打款", paid: "已打款", rejected: "已驳回" };
onMounted(distribution.loadAll);
</script>

<template>
  <section class="mx-auto max-w-7xl space-y-5">
    <DistributionSummary :overview="distribution.overview" @withdraw="distribution.withdrawalOpen.value = true" />
    <div class="border-b border-slate-200"><button v-for="item in tabs" :key="item.key" type="button" class="border-b-2 px-4 py-3 text-xs font-bold" :class="tab === item.key ? 'border-primary text-primary' : 'border-transparent text-slate-500'" @click="tab = item.key">{{ item.label }}</button></div>
    <DistributionDownlines v-if="tab === 'downlines'" :state="distribution.downlines" :own-rate="Number(distribution.overview.commission_rate)" :level="Number(distribution.overview.level)" @update-rate="distribution.updateRate" @change-page="distribution.changeDownlinesPage" />
    <div v-else class="rounded-lg border border-slate-200 bg-white"><div class="overflow-x-auto"><table class="w-full text-left text-xs"><thead class="bg-slate-50 text-slate-400"><tr><th class="px-4 py-3">时间</th><th class="px-4 py-3">类型</th><th class="px-4 py-3">金额</th><th class="px-4 py-3">状态/说明</th></tr></thead><tbody><template v-if="tab === 'transactions'"><tr v-for="item in distribution.transactions.items" :key="item.id" class="border-t border-slate-100"><td class="px-4 py-3">{{ formatTime(item.created_at) }}</td><td class="px-4 py-3 font-bold">{{ item.type }}</td><td class="px-4 py-3 font-black" :class="item.available_delta_cents >= 0 ? 'text-emerald-600' : 'text-rose-600'">{{ formatMoney(item.available_delta_cents) }}</td><td class="px-4 py-3 text-slate-500">{{ item.note }}</td></tr></template><template v-else><tr v-for="item in distribution.withdrawals.items" :key="item.id" class="border-t border-slate-100"><td class="px-4 py-3">{{ formatTime(item.created_at) }}</td><td class="px-4 py-3 font-bold">提现申请</td><td class="px-4 py-3 font-black text-slate-800">{{ formatMoney(item.amount_cents) }}</td><td class="px-4 py-3 text-slate-500">{{ withdrawalStatus[item.status] }}<span v-if="item.reject_reason"> · {{ item.reject_reason }}</span></td></tr></template></tbody></table></div><div class="border-t border-slate-100 p-4"><AppPagination :state="tab === 'transactions' ? distribution.transactions : distribution.withdrawals" @change-page="tab === 'transactions' ? distribution.changeTransactionsPage($event) : distribution.changeWithdrawalsPage($event)" /></div></div>
    <WithdrawalModal :open="distribution.withdrawalOpen.value" :saving="distribution.saving.value" @close="distribution.withdrawalOpen.value = false" @submit="distribution.submitWithdrawal" />
  </section>
</template>
