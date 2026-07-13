<script setup>
import { formatMoney, formatTime, orderStatusLabel, orderStatusOptions } from "@/constants/admin.js";
import AdminFilterBar from "@/components/admin/common/AdminFilterBar.vue";
import AdminSearchInput from "@/components/admin/common/AdminSearchInput.vue";
import AdminTableStateRow from "@/components/admin/common/AdminTableStateRow.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AppPagination from "@/components/ui/AppPagination.vue";

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
    <AdminFilterBar :total="state.total" total-label="个订单" @apply-filter="emit('apply-filter')">
      <AdminSearchInput v-model="state.keyword" placeholder="搜索邮箱或订单号" @search="emit('apply-filter')" />
      <div class="w-36">
        <AppSelect v-model="state.status" :options="orderStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
    </AdminFilterBar>

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
          <AdminTableStateRow v-if="state.loading || !state.items.length" :loading="state.loading" :empty="!state.items.length" :colspan="6" empty-text="暂无订单" />
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
            <td class="px-4 py-3 text-slate-600">{{ orderStatusLabel(order.status) }}</td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(order.paid_at || order.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <AppPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
