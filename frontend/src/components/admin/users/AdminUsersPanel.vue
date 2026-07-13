<script setup>
import {
  formatTime,
  roleLabel,
  statusLabel,
  userRoleOptions,
  userStatusOptions,
} from "@/constants/admin.js";
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

const emit = defineEmits([
  "apply-filter",
  "adjust-credits",
  "business-settings",
  "reset-password",
  "change-role",
  "change-status",
  "change-page",
]);
</script>

<template>
  <section class="space-y-4">
    <AdminFilterBar :total="state.total" total-label="个用户" @apply-filter="emit('apply-filter')">
      <AdminSearchInput v-model="state.keyword" placeholder="搜索邮箱或用户名" @search="emit('apply-filter')" />
      <div class="w-36">
        <AppSelect v-model="state.role" :options="userRoleOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-36">
        <AppSelect v-model="state.status" :options="userStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
    </AdminFilterBar>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">用户</th>
            <th class="px-4 py-3 font-semibold">角色</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">积分</th>
            <th class="px-4 py-3 font-semibold">倍率</th>
            <th class="px-4 py-3 font-semibold">分销</th>
            <th class="px-4 py-3 font-semibold">注册时间</th>
            <th class="px-4 py-3 text-right font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <AdminTableStateRow v-if="state.loading || !state.items.length" :loading="state.loading" :empty="!state.items.length" :colspan="8" empty-text="暂无用户" />
          <tr v-for="user in state.items" v-else :key="user.id" class="border-t border-slate-100">
            <td class="px-4 py-3">
              <p class="font-bold text-slate-800">{{ user.email }}</p>
              <p class="mt-0.5 text-slate-400">ID {{ user.id }} · {{ user.username }}</p>
            </td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-1 text-[11px] font-bold" :class="user.role === 'super_admin' ? 'bg-primary/10 text-primary' : 'bg-slate-100 text-slate-500'">
                {{ roleLabel(user.role) }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-1 text-[11px] font-bold" :class="user.status === 'disabled' ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'">
                {{ statusLabel(user.status) }}
              </span>
            </td>
            <td class="px-4 py-3 font-black text-primary">{{ user.credits }} 点</td>
            <td class="px-4 py-3 font-bold text-slate-700">{{ Number(user.consumption_multiplier || 1).toFixed(2) }}×</td>
            <td class="px-4 py-3 text-slate-500">{{ user.distribution_level ? `${user.distribution_level}级 · ${user.distribution_enabled ? '启用' : '停止'}` : '-' }}</td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(user.created_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="emit('adjust-credits', user)">
                  调积分
                </button>
                <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="emit('business-settings', user)">业务</button>
                <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="emit('reset-password', user)">重置密码</button>
                <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="emit('change-role', user)">
                  {{ user.role === 'super_admin' ? '取消超管' : '设为超管' }}
                </button>
                <button type="button" class="rounded-lg border px-2.5 py-1.5 font-semibold" :class="user.status === 'disabled' ? 'border-emerald-200 text-emerald-600 hover:bg-emerald-50' : 'border-rose-200 text-rose-600 hover:bg-rose-50'" @click="emit('change-status', user)">
                  {{ user.status === 'disabled' ? '启用' : '禁用' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AppPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
