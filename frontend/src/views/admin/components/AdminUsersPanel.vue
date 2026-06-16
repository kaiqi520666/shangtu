<script setup>
import { LoaderCircle, Search } from "lucide-vue-next";
import { formatTime, roleLabel, statusLabel } from "../adminFormatters.js";
import AdminPagination from "./AdminPagination.vue";

defineProps({
  state: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits([
  "apply-filter",
  "adjust-credits",
  "change-role",
  "change-status",
  "change-page",
]);
</script>

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div class="flex min-w-64 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
        <Search class="h-4 w-4 text-slate-300" />
        <input
          v-model="state.keyword"
          type="text"
          class="w-full border-0 bg-transparent text-xs outline-none"
          placeholder="搜索邮箱或用户名"
          @keyup.enter="emit('apply-filter')"
        />
      </div>
      <select v-model="state.role" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs" @change="emit('apply-filter')">
        <option value="">全部角色</option>
        <option value="user">普通用户</option>
        <option value="super_admin">超级管理员</option>
      </select>
      <select v-model="state.status" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs" @change="emit('apply-filter')">
        <option value="">全部状态</option>
        <option value="active">正常</option>
        <option value="disabled">已禁用</option>
      </select>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">
        查询
      </button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个用户</span>
    </div>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">用户</th>
            <th class="px-4 py-3 font-semibold">角色</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">积分</th>
            <th class="px-4 py-3 font-semibold">注册时间</th>
            <th class="px-4 py-3 text-right font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading">
            <td colspan="6" class="px-4 py-10 text-center text-slate-400">
              <LoaderCircle class="mx-auto mb-2 h-5 w-5 animate-spin" />
              加载中...
            </td>
          </tr>
          <tr v-else-if="!state.items.length">
            <td colspan="6" class="px-4 py-10 text-center text-slate-400">暂无用户</td>
          </tr>
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
            <td class="px-4 py-3 text-slate-500">{{ formatTime(user.created_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-2">
                <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="emit('adjust-credits', user)">
                  调积分
                </button>
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

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
