<script setup>
import { LoaderCircle, Plus, Search } from "lucide-vue-next";
import AdminPagination from "@/components/admin/AdminPagination.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { couponStatusOptions, formatTime } from "@/constants/admin.js";

defineProps({ state: { type: Object, required: true } });
const emit = defineEmits(["apply-filter", "change-page", "create", "delete", "edit", "toggle", "update-keyword", "update-status"]);
</script>

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div class="flex min-w-64 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
        <Search class="h-4 w-4 text-slate-300" />
        <input :value="state.keyword" type="text" class="w-full border-0 bg-transparent text-xs outline-none" placeholder="搜索优惠码" @input="emit('update-keyword', $event.target.value)" @keyup.enter="emit('apply-filter')" />
      </div>
      <div class="w-36">
        <AppSelect :model-value="state.status" :options="couponStatusOptions" @update:model-value="emit('update-status', $event); emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个优惠码</span>
      <button type="button" class="inline-flex items-center gap-1.5 rounded-lg bg-slate-950 px-3 py-2 text-xs font-bold text-white" @click="emit('create')">
        <Plus class="h-4 w-4" />
        创建优惠码
      </button>
    </div>

    <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full min-w-[900px] text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">优惠码</th>
            <th class="px-4 py-3 font-semibold">赠送积分</th>
            <th class="px-4 py-3 font-semibold">使用情况</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">创建人</th>
            <th class="px-4 py-3 font-semibold">创建时间</th>
            <th class="px-4 py-3 text-right font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading"><td colspan="7" class="px-4 py-12 text-center text-slate-400"><LoaderCircle class="mx-auto mb-2 h-5 w-5 animate-spin" />加载中...</td></tr>
          <tr v-else-if="!state.items.length"><td colspan="7" class="px-4 py-12 text-center text-slate-400">暂无优惠码</td></tr>
          <tr v-for="item in state.items" v-else :key="item.id" class="border-t border-slate-100">
            <td class="px-4 py-3 font-black tracking-normal text-slate-900">{{ item.code }}</td>
            <td class="px-4 py-3 font-black text-primary">{{ item.credits.toLocaleString() }} 点</td>
            <td class="px-4 py-3 font-semibold text-slate-600">{{ item.used_count }} / {{ item.usage_limit ?? "无限" }}</td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-1 text-[11px] font-bold" :class="item.deleted_at ? 'bg-slate-100 text-slate-500' : item.enabled ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'">{{ item.deleted_at ? "已删除" : item.enabled ? "启用" : "停用" }}</span>
            </td>
            <td class="px-4 py-3 text-slate-500">{{ item.created_by_email || `ID ${item.created_by_user_id}` }}</td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(item.created_at) }}</td>
            <td class="px-4 py-3">
              <div v-if="!item.deleted_at" class="flex justify-end gap-2">
                <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="emit('edit', item)">编辑</button>
                <button type="button" class="rounded-lg border px-2.5 py-1.5 font-semibold" :class="item.enabled ? 'border-amber-200 text-amber-600' : 'border-emerald-200 text-emerald-600'" @click="emit('toggle', item)">{{ item.enabled ? "停用" : "启用" }}</button>
                <button type="button" class="rounded-lg border border-rose-200 px-2.5 py-1.5 font-semibold text-rose-600" @click="emit('delete', item)">删除</button>
              </div>
              <span v-else class="block text-right text-slate-300">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
