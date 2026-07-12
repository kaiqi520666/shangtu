<script setup>
import { LoaderCircle, Search } from "lucide-vue-next";
import AdminPagination from "@/components/admin/AdminPagination.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { formatMoney, formatTime } from "@/constants/admin.js";

defineProps({ state: { type: Object, required: true } });
const emit = defineEmits(["filter", "page", "approve", "reject", "pay", "update-keyword", "update-status"]);
const statusOptions = [
  { label: "全部状态", value: "" },
  { label: "待审核", value: "pending_review" },
  { label: "待打款", value: "pending_payment" },
  { label: "已打款", value: "paid" },
  { label: "已驳回", value: "rejected" },
];
const statusLabels = { pending_review: "待审核", pending_payment: "待打款", paid: "已打款", rejected: "已驳回" };
</script>

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white p-3">
      <div class="flex min-w-64 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2"><Search class="h-4 w-4 text-slate-300" /><input :value="state.keyword" class="w-full text-xs outline-none" placeholder="搜索用户或支付宝" @input="emit('update-keyword', $event.target.value)" @keyup.enter="emit('filter')" /></div>
      <div class="w-36"><AppSelect :model-value="state.status" :options="statusOptions" @update:model-value="emit('update-status', $event); emit('filter')" /></div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('filter')">查询</button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 条</span>
    </div>
    <div class="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table class="w-full min-w-[980px] text-left text-xs">
        <thead class="bg-slate-50 text-slate-400"><tr><th class="px-4 py-3">用户</th><th class="px-4 py-3">金额</th><th class="px-4 py-3">支付宝</th><th class="px-4 py-3">状态</th><th class="px-4 py-3">申请时间</th><th class="px-4 py-3 text-right">操作</th></tr></thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="6" class="px-4 py-12 text-center text-slate-400"><LoaderCircle class="mx-auto h-5 w-5 animate-spin" /></td></tr>
          <tr v-else-if="!state.items.length"><td colspan="6" class="px-4 py-12 text-center text-slate-400">暂无提现申请</td></tr>
          <tr v-for="item in state.items" v-else :key="item.id" class="border-t border-slate-100">
            <td class="px-4 py-3 font-bold text-slate-800">{{ item.user_email }}</td><td class="px-4 py-3 text-sm font-black text-primary">{{ formatMoney(item.amount_cents) }}</td><td class="px-4 py-3 text-slate-600"><p>{{ item.alipay_name }}</p><p class="text-slate-400">{{ item.alipay_account }}</p></td><td class="px-4 py-3 font-bold text-slate-600">{{ statusLabels[item.status] }}</td><td class="px-4 py-3 text-slate-500">{{ formatTime(item.created_at) }}</td>
            <td class="px-4 py-3"><div class="flex justify-end gap-2"><button v-if="item.status === 'pending_review'" class="rounded-lg border border-emerald-200 px-2.5 py-1.5 font-bold text-emerald-600" @click="emit('approve', item)">通过</button><button v-if="['pending_review', 'pending_payment'].includes(item.status)" class="rounded-lg border border-rose-200 px-2.5 py-1.5 font-bold text-rose-600" @click="emit('reject', item)">驳回</button><button v-if="item.status === 'pending_payment'" class="rounded-lg bg-primary px-2.5 py-1.5 font-bold text-white" @click="emit('pay', item)">确认打款</button></div></td>
          </tr>
        </tbody>
      </table>
      <div class="border-t border-slate-100 p-4"><AdminPagination :state="state" @change-page="emit('page', $event)" /></div>
    </div>
  </section>
</template>
