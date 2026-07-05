<script setup>
import { LoaderCircle, RefreshCw } from "lucide-vue-next";
import { activeStatusLabel, activeStatusOptions, formatTime } from "@/constants/admin.js";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AdminPagination from "@/components/admin/AdminPagination.vue";

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
    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <input v-model="state.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索名称、voice_id、语言" @keyup.enter="emit('apply-filter')" />
      <div class="w-32">
        <AppSelect v-model="state.active" :options="activeStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <button type="button" class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50" :disabled="syncing || state.loading" @click="emit('sync')">
        <LoaderCircle v-if="syncing" class="h-3.5 w-3.5 animate-spin" />
        <RefreshCw v-else class="h-3.5 w-3.5" />
        {{ syncing ? "同步中..." : "同步 HeyGen" }}
      </button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个系统声音</span>
    </div>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">声音</th>
            <th class="px-4 py-3 font-semibold">语言 / 性别</th>
            <th class="px-4 py-3 font-semibold">试听</th>
            <th class="px-4 py-3 font-semibold">能力</th>
            <th class="px-4 py-3 font-semibold">排序</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">更新时间</th>
            <th class="px-4 py-3 font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading">
            <td colspan="8" class="px-4 py-10 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="!state.items.length">
            <td colspan="8" class="px-4 py-10 text-center text-slate-400">暂无系统声音</td>
          </tr>
          <tr v-for="item in state.items" v-else :key="item.id" class="border-t border-slate-100 align-top">
            <td class="px-4 py-3">
              <p class="font-bold text-slate-800">{{ item.name }}</p>
              <p class="mt-0.5 text-slate-400">{{ item.voice_id }}</p>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ item.language || "-" }} / {{ item.gender || "-" }}</td>
            <td class="px-4 py-3">
              <audio v-if="item.preview_audio_url" :src="item.preview_audio_url" controls preload="none" class="h-8 w-52"></audio>
              <span v-else class="text-slate-400">暂无试听</span>
            </td>
            <td class="px-4 py-3 text-slate-500">
              <p>Locale：{{ item.support_locale ? "支持" : "不支持" }}</p>
              <p class="mt-0.5">Pause：{{ item.support_pause ? "支持" : "不支持" }}</p>
            </td>
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

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
