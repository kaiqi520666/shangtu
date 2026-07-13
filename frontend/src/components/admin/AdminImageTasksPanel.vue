<script setup>
import {
  formatTime,
  imageTaskStatusLabel,
  imageTaskStatusOptions,
  scenarioLabel,
  scenarioOptions,
  taskMediaTypeOptions,
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

const emit = defineEmits(["apply-filter", "change-page"]);
</script>

<template>
  <section class="space-y-4">
    <AdminFilterBar :total="state.total" total-label="个任务" @apply-filter="emit('apply-filter')">
      <AdminSearchInput v-model="state.keyword" placeholder="搜索邮箱、任务ID、标题或上游ID" @search="emit('apply-filter')" />
      <div class="w-36">
        <AppSelect v-model="state.status" :options="imageTaskStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-36">
        <AppSelect v-model="state.scenario" :options="scenarioOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-32">
        <AppSelect v-model="state.mediaType" :options="taskMediaTypeOptions" @update:model-value="emit('apply-filter')" />
      </div>
    </AdminFilterBar>

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
          <AdminTableStateRow v-if="state.loading || !state.items.length" :loading="state.loading" :empty="!state.items.length" :colspan="7" empty-text="暂无生成任务" />
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

    <AppPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
