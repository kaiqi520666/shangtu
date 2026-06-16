<script setup>
import { formatMoney, formatTime } from "../adminFormatters.js";
import AdminPagination from "./AdminPagination.vue";

defineProps({
  state: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["apply-filter", "change-page"]);
</script>

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <input v-model="state.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索邮箱或订单号" @keyup.enter="emit('apply-filter')" />
      <select v-model="state.status" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs" @change="emit('apply-filter')">
        <option value="">全部状态</option>
        <option value="pending">待支付</option>
        <option value="paid">已支付</option>
        <option value="failed">失败</option>
      </select>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个订单</span>
    </div>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">订单</th>
            <th class="px-4 py-3 font-semibold">用户</th>
            <th class="px-4 py-3 font-semibold">套餐</th>
            <th class="px-4 py-3 font-semibold">金额</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading">
            <td colspan="6" class="px-4 py-10 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="!state.items.length">
            <td colspan="6" class="px-4 py-10 text-center text-slate-400">暂无订单</td>
          </tr>
          <tr v-for="order in state.items" v-else :key="order.id" class="border-t border-slate-100">
            <td class="px-4 py-3">
              <p class="font-bold text-slate-800">{{ order.out_trade_no }}</p>
              <p class="mt-0.5 text-slate-400">{{ order.provider_trade_no || '-' }}</p>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ order.user_email || order.user_id }}</td>
            <td class="px-4 py-3">
              <p class="font-bold text-slate-800">{{ order.package_name }}</p>
              <p class="mt-0.5 text-primary">{{ order.credits }} 点</p>
            </td>
            <td class="px-4 py-3 font-bold text-slate-800">{{ formatMoney(order.amount_cents) }}</td>
            <td class="px-4 py-3 text-slate-600">{{ order.status }}</td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(order.paid_at || order.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
