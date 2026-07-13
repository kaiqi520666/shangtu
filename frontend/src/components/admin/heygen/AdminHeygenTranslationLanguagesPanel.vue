<script setup>
import { LoaderCircle, RefreshCw } from "lucide-vue-next";
import {
  activeStatusLabel,
  activeStatusOptions,
  formatTime,
} from "@/constants/admin.js";
import AdminFilterBar from "@/components/admin/common/AdminFilterBar.vue";
import AdminSearchInput from "@/components/admin/common/AdminSearchInput.vue";
import AdminTableStateRow from "@/components/admin/common/AdminTableStateRow.vue";
import AppPagination from "@/components/ui/AppPagination.vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppSelect from "@/components/ui/AppSelect.vue";

defineProps({
  state: {
    type: Object,
    required: true,
  },
  syncing: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["apply-filter", "change-page", "edit", "toggle", "sync"]);
</script>

<template>
  <section class="space-y-4">
    <AdminFilterBar :total="state.total" total-label="个翻译语言" @apply-filter="emit('apply-filter')">
      <AdminSearchInput v-model="state.keyword" placeholder="搜索原始名、中文名" @search="emit('apply-filter')" />
      <div class="w-32">
        <AppSelect v-model="state.active" :options="activeStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <template #actions>
        <button type="button" class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50" :disabled="syncing || state.loading" @click="emit('sync')">
          <LoaderCircle v-if="syncing" class="h-3.5 w-3.5 animate-spin" />
          <RefreshCw v-else class="h-3.5 w-3.5" />
          {{ syncing ? "同步中..." : "同步 HeyGen" }}
        </button>
      </template>
    </AdminFilterBar>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">中文展示名</th>
            <th class="px-4 py-3 font-semibold">HeyGen 原始名</th>
            <th class="px-4 py-3 font-semibold">排序</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">更新时间</th>
            <th class="px-4 py-3 font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <AdminTableStateRow v-if="state.loading || !state.items.length" :loading="state.loading" :empty="!state.items.length" :colspan="6" empty-text="暂无翻译语言" />
          <tr v-for="item in state.items" v-else :key="item.id" class="border-t border-slate-100 align-top">
            <td class="px-4 py-3 font-bold text-slate-800">{{ item.display_name_zh }}</td>
            <td class="px-4 py-3 text-slate-500">{{ item.name }}</td>
            <td class="px-4 py-3 text-slate-500">{{ item.sort_order }}</td>
            <td class="px-4 py-3">
              <AppCheckbox :model-value="item.enabled" :label="activeStatusLabel(item.enabled)" @change="emit('toggle', item)" />
            </td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(item.updated_at || item.created_at) }}</td>
            <td class="px-4 py-3">
              <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('edit', item)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AppPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
