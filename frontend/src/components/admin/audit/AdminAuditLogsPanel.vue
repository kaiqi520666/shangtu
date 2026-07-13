<script setup>
import { auditActionLabel, auditActionOptions, formatTime } from "@/constants/admin.js";
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
    <AdminFilterBar :total="state.total" total-label="条日志" @apply-filter="emit('apply-filter')">
      <AdminSearchInput v-model="state.keyword" placeholder="搜索管理员、目标、操作或详情" @search="emit('apply-filter')" />
      <div class="w-36">
        <AppSelect v-model="state.action" :options="auditActionOptions" @update:model-value="emit('apply-filter')" />
      </div>
    </AdminFilterBar>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">管理员</th>
            <th class="px-4 py-3 font-semibold">操作</th>
            <th class="px-4 py-3 font-semibold">目标</th>
            <th class="px-4 py-3 font-semibold">详情</th>
            <th class="px-4 py-3 font-semibold">时间</th>
          </tr>
        </thead>
        <tbody>
          <AdminTableStateRow v-if="state.loading || !state.items.length" :loading="state.loading" :empty="!state.items.length" :colspan="5" empty-text="暂无审计日志" />
          <tr v-for="log in state.items" v-else :key="log.id" class="border-t border-slate-100 align-top">
            <td class="px-4 py-3 text-slate-600">{{ log.actor_email || log.actor_user_id }}</td>
            <td class="px-4 py-3 font-bold text-slate-800">{{ auditActionLabel(log.action) }}</td>
            <td class="px-4 py-3">
              <p class="text-slate-700">{{ log.target_type || '-' }}</p>
              <p class="mt-0.5 max-w-44 truncate text-slate-400">{{ log.target_id || '-' }}</p>
            </td>
            <td class="px-4 py-3">
              <pre class="max-w-md whitespace-pre-wrap rounded-lg bg-slate-50 px-3 py-2 text-[11px] leading-relaxed text-slate-500">{{ JSON.stringify(log.detail || {}, null, 2) }}</pre>
            </td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(log.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <AppPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
