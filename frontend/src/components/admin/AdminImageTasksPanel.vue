<script setup>
import {
  formatTime,
  imageTaskStatusLabel,
  imageTaskStatusOptions,
  scenarioLabel,
  scenarioOptions,
  taskMediaTypeOptions,
} from "@/constants/admin.js";
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
      <input v-model="state.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索邮箱、任务ID、标题或上游ID" @keyup.enter="emit('apply-filter')" />
      <div class="w-36">
        <AppSelect v-model="state.status" :options="imageTaskStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-36">
        <AppSelect v-model="state.scenario" :options="scenarioOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-32">
        <AppSelect v-model="state.mediaType" :options="taskMediaTypeOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个任务</span>
    </div>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">任务</th>
            <th class="px-4 py-3 font-semibold">用户</th>
            <th class="px-4 py-3 font-semibold">场景</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">扣费</th>
            <th class="px-4 py-3 font-semibold">上游</th>
            <th class="px-4 py-3 font-semibold">时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading">
            <td colspan="7" class="px-4 py-10 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="!state.items.length">
            <td colspan="7" class="px-4 py-10 text-center text-slate-400">暂无生成任务</td>
          </tr>
          <tr v-for="task in state.items" v-else :key="task.id" class="border-t border-slate-100 align-top">
            <td class="px-4 py-3">
              <p class="font-bold text-slate-800">{{ task.title || task.type_id || '未命名任务' }}</p>
              <p class="mt-0.5 max-w-72 truncate text-slate-400">{{ task.id }}</p>
              <p class="mt-0.5 text-[11px] font-semibold" :class="task.media_type === 'video' ? 'text-violet-500' : 'text-sky-500'">
                {{ task.media_type === 'video' ? '视频任务' : '图片任务' }}
              </p>
              <p v-if="task.error_message" class="mt-1 max-w-72 truncate text-rose-500">{{ task.error_message }}</p>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ task.user_email || task.user_id }}</td>
            <td class="px-4 py-3">
              <p class="font-semibold text-slate-700">{{ scenarioLabel(task.scenario) }}</p>
              <p class="mt-0.5 text-slate-400">{{ task.size || '-' }}</p>
            </td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-1 text-[11px] font-bold" :class="task.status === 'done' ? 'bg-emerald-50 text-emerald-600' : task.status === 'failed' || task.status === 'timeout' ? 'bg-rose-50 text-rose-600' : 'bg-amber-50 text-amber-600'">
                {{ imageTaskStatusLabel(task.status) }}
              </span>
              <p class="mt-1 text-slate-400">{{ task.progress || 0 }}%</p>
            </td>
            <td class="px-4 py-3">
              <p class="font-bold text-primary">{{ task.credit_cost }} 点</p>
              <p class="mt-0.5 text-slate-400">{{ task.credit_refunded ? '已退款' : '未退款' }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="text-slate-600">{{ task.provider || '-' }}</p>
              <p class="mt-0.5 max-w-48 truncate text-slate-400">{{ task.provider_task_id || '-' }}</p>
            </td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(task.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
