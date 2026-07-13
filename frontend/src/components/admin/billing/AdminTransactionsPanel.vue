<script setup>
import { formatTime, transactionTypeLabel, transactionTypeOptions } from "@/constants/admin.js";
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
    <AdminFilterBar :total="state.total" total-label="条流水" @apply-filter="emit('apply-filter')">
      <AdminSearchInput v-model="state.keyword" placeholder="搜索邮箱或备注" @search="emit('apply-filter')" />
      <div class="w-36">
        <AppSelect v-model="state.type" :options="transactionTypeOptions" @update:model-value="emit('apply-filter')" />
      </div>
    </AdminFilterBar>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">用户</th>
            <th class="px-4 py-3 font-semibold">类型</th>
            <th class="px-4 py-3 font-semibold">变动</th>
            <th class="px-4 py-3 font-semibold">余额</th>
            <th class="px-4 py-3 font-semibold">备注</th>
            <th class="px-4 py-3 font-semibold">时间</th>
          </tr>
        </thead>
        <tbody>
          <AdminTableStateRow v-if="state.loading || !state.items.length" :loading="state.loading" :empty="!state.items.length" :colspan="6" empty-text="暂无流水" />
          <tr v-for="tx in state.items" v-else :key="tx.id" class="border-t border-slate-100">
            <td class="px-4 py-3 text-slate-600">{{ tx.user_email || tx.user_id }}</td>
            <td class="px-4 py-3">{{ transactionTypeLabel(tx.type) }}</td>
            <td class="px-4 py-3 font-black" :class="tx.credits_delta >= 0 ? 'text-emerald-600' : 'text-rose-600'">
              {{ tx.credits_delta >= 0 ? '+' : '' }}{{ tx.credits_delta }}
            </td>
            <td class="px-4 py-3 font-bold text-slate-800">{{ tx.balance_after }} 点</td>
            <td class="px-4 py-3 text-slate-500">{{ tx.note || '-' }}</td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(tx.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <AppPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
