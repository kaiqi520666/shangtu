<script setup>
import { formatTime, transactionTypeLabel, transactionTypeOptions } from "@/constants/admin.js";
import AppSelect from "@/components/ui/AppSelect.vue";
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
      <input
        v-model="state.keyword"
        type="text"
        class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none"
        placeholder="搜索邮箱或备注"
        @keyup.enter="emit('apply-filter')"
      />
      <div class="w-36">
        <AppSelect v-model="state.type" :options="transactionTypeOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">
        查询
      </button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 条流水</span>
    </div>

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
          <tr v-if="state.loading">
            <td colspan="6" class="px-4 py-10 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="!state.items.length">
            <td colspan="6" class="px-4 py-10 text-center text-slate-400">暂无流水</td>
          </tr>
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

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
